import asyncio
import hashlib
import hmac
import os
import time
import uuid
from collections import OrderedDict, defaultdict, deque
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import report
import scanner
from i18n import lang_of, t

MAX_TARGETS = 4
MAX_CONCURRENT_HOSTS = int(os.environ.get("MAX_CONCURRENT_HOSTS", "4"))
RATE_LIMIT = int(os.environ.get("RATE_LIMIT_HOSTS", "40"))  # hosts per IP per window
RATE_WINDOW = 600
PASSWORD = os.environ.get("SCAN_PASSWORD", "")
MAX_BAD_PASSWORD = 10  # per IP per window
CACHE_SIZE = 200

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
STATIC = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


def _asset_version():
    # Content hash of the cached assets, so a deploy changes their URLs and no edge cache serves stale copies.
    h = hashlib.sha256()
    for path in ("app.css", "app.js", "contoh/miraestudio-id.pdf", "contoh/miraestudio-id-en.pdf"):
        with open(os.path.join(STATIC, path), "rb") as f:
            h.update(f.read())
    return h.hexdigest()[:10]


ASSET_V = _asset_version()
PAGES = {}
for _name in ("index.html", "metodologi.html", "en/index.html", "en/methodology.html"):
    with open(os.path.join(STATIC, _name), encoding="utf-8") as _f:
        PAGES[_name] = _f.read().replace("?v=ASSET", f"?v={ASSET_V}")

_sem = asyncio.Semaphore(MAX_CONCURRENT_HOSTS)
_scans: "OrderedDict[str, dict]" = OrderedDict()
_hits: "defaultdict[str, deque]" = defaultdict(deque)
_bad: "defaultdict[str, deque]" = defaultdict(deque)


class ScanRequest(BaseModel):
    targets: list[str]
    checks: list[str] = list(scanner.CHECKS)
    lang: str = "id"


def _client_ip(req: Request):
    return req.headers.get("cf-connecting-ip") or (req.client.host if req.client else "?")


def _rate_limit(ip, n, lang):
    now = time.time()
    q = _hits[ip]
    while q and q[0] < now - RATE_WINDOW:
        q.popleft()
    if len(q) + n > RATE_LIMIT:
        raise HTTPException(429, t(lang, "api_rate"))
    q.extend([now] * n)


def _check_password(ip, given, lang):
    if not PASSWORD:
        return
    now = time.time()
    q = _bad[ip]
    while q and q[0] < now - RATE_WINDOW:
        q.popleft()
    if len(q) >= MAX_BAD_PASSWORD:
        raise HTTPException(429, t(lang, "api_bad_pw_rate"))
    if not hmac.compare_digest((given or "").encode(), PASSWORD.encode()):
        q.append(now)
        raise HTTPException(401, t(lang, "api_bad_pw"))


async def _scan_one(target, checks, lang):
    async with _sem:
        return await asyncio.to_thread(scanner.scan_target, target, checks, lang)


@app.get("/")
def index():
    return HTMLResponse(PAGES["index.html"])


@app.get("/metodologi")
def methodology():
    return HTMLResponse(PAGES["metodologi.html"])


@app.get("/en")
def index_en():
    return HTMLResponse(PAGES["en/index.html"])


@app.get("/en/methodology")
def methodology_en():
    return HTMLResponse(PAGES["en/methodology.html"])


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.post("/api/scan")
async def scan(body: ScanRequest, req: Request):
    lang = lang_of(body.lang)
    targets = []
    for target in body.targets:
        target = target.strip()
        if target and target not in targets:
            targets.append(target[:300])
    if not targets:
        raise HTTPException(400, t(lang, "api_no_target"))
    if len(targets) > MAX_TARGETS:
        raise HTTPException(400, t(lang, "api_too_many", n=MAX_TARGETS))
    checks = [c for c in scanner.CHECKS if c in body.checks]
    if not checks:
        raise HTTPException(400, t(lang, "api_no_check"))
    ip = _client_ip(req)
    _check_password(ip, req.headers.get("x-scan-password"), lang)
    _rate_limit(ip, len(targets), lang)

    results = await asyncio.gather(*(_scan_one(target, checks, lang) for target in targets))
    scan_id = uuid.uuid4().hex
    data = {
        "id": scan_id,
        "lang": lang,
        "created": datetime.now(scanner.WIB).isoformat(),
        "results": results,
        "summary": scanner.summarize(results),
    }
    _scans[scan_id] = data
    while len(_scans) > CACHE_SIZE:
        _scans.popitem(last=False)
    return data


@app.get("/api/report/{scan_id}.pdf")
async def pdf(scan_id: str, lang: str = "id"):
    data = _scans.get(scan_id)
    if not data:
        raise HTTPException(404, t(lang, "api_expired"))
    pdf_bytes = await asyncio.to_thread(report.build_pdf, data)
    hosts = ", ".join(r.get("host") or r["target"] for r in data["results"])[:80]
    stamp = datetime.fromisoformat(data["created"]).strftime("%Y.%m.%d %H.%M.%S")
    title = "PQC Readiness Scan" if data.get("lang") == "en" else "Hasil Scan Kesiapan PQC"
    name = f"{title} {hosts} {stamp}.pdf".replace('"', "")
    return Response(pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{name}"'})
