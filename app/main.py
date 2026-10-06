import asyncio
import hmac
import os
import time
import uuid
from collections import OrderedDict, defaultdict, deque
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

import report
import scanner

MAX_TARGETS = 4
MAX_CONCURRENT_HOSTS = int(os.environ.get("MAX_CONCURRENT_HOSTS", "4"))
RATE_LIMIT = int(os.environ.get("RATE_LIMIT_HOSTS", "40"))  # hosts per IP per window
RATE_WINDOW = 600
PASSWORD = os.environ.get("SCAN_PASSWORD", "")
MAX_BAD_PASSWORD = 10  # per IP per window
CACHE_SIZE = 200

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
STATIC = os.path.join(os.path.dirname(__file__), "static")

_sem = asyncio.Semaphore(MAX_CONCURRENT_HOSTS)
_scans: "OrderedDict[str, dict]" = OrderedDict()
_hits: "defaultdict[str, deque]" = defaultdict(deque)
_bad: "defaultdict[str, deque]" = defaultdict(deque)


class ScanRequest(BaseModel):
    targets: list[str]
    checks: list[str] = list(scanner.CHECKS)


def _client_ip(req: Request):
    return req.headers.get("cf-connecting-ip") or (req.client.host if req.client else "?")


def _rate_limit(ip, n):
    now = time.time()
    q = _hits[ip]
    while q and q[0] < now - RATE_WINDOW:
        q.popleft()
    if len(q) + n > RATE_LIMIT:
        raise HTTPException(429, "Terlalu banyak scan. Coba lagi beberapa menit lagi.")
    q.extend([now] * n)


def _check_password(ip, given):
    if not PASSWORD:
        return
    now = time.time()
    q = _bad[ip]
    while q and q[0] < now - RATE_WINDOW:
        q.popleft()
    if len(q) >= MAX_BAD_PASSWORD:
        raise HTTPException(429, "Terlalu banyak percobaan password salah. Coba lagi nanti.")
    if not hmac.compare_digest((given or "").encode(), PASSWORD.encode()):
        q.append(now)
        raise HTTPException(401, "Password salah.")


async def _scan_one(target, checks):
    async with _sem:
        return await asyncio.to_thread(scanner.scan_target, target, checks)


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC, "index.html"))


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.post("/api/scan")
async def scan(body: ScanRequest, req: Request):
    targets = []
    for t in body.targets:
        t = t.strip()
        if t and t not in targets:
            targets.append(t[:300])
    if not targets:
        raise HTTPException(400, "Masukkan minimal satu domain atau IP.")
    if len(targets) > MAX_TARGETS:
        raise HTTPException(400, f"Maksimal {MAX_TARGETS} target per scan.")
    checks = [c for c in scanner.CHECKS if c in body.checks]
    if not checks:
        raise HTTPException(400, "Pilih minimal satu metode testing.")
    ip = _client_ip(req)
    _check_password(ip, req.headers.get("x-scan-password"))
    _rate_limit(ip, len(targets))

    results = await asyncio.gather(*(_scan_one(t, checks) for t in targets))
    scan_id = uuid.uuid4().hex
    data = {
        "id": scan_id,
        "created": datetime.now(scanner.WIB).isoformat(),
        "results": results,
        "summary": scanner.summarize(results),
    }
    _scans[scan_id] = data
    while len(_scans) > CACHE_SIZE:
        _scans.popitem(last=False)
    return data


@app.get("/api/report/{scan_id}.pdf")
async def pdf(scan_id: str):
    data = _scans.get(scan_id)
    if not data:
        raise HTTPException(404, "Hasil scan sudah kedaluwarsa, silakan scan ulang.")
    pdf_bytes = await asyncio.to_thread(report.build_pdf, data)
    hosts = ", ".join(r.get("host") or r["target"] for r in data["results"])[:80]
    stamp = datetime.fromisoformat(data["created"]).strftime("%Y.%m.%d %H.%M.%S")
    name = f"Hasil Scan Kesiapan PQC {hosts} {stamp}.pdf".replace('"', "")
    return Response(pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{name}"'})
