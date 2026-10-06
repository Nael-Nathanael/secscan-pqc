import re

import pytest
from fastapi.testclient import TestClient

import main
import scanner


@pytest.fixture
def client():
    return TestClient(main.app)


def test_pages_and_assets(client):
    for path in ("/", "/metodologi", "/static/app.css", "/healthz"):
        assert client.get(path).status_code == 200, path


def test_asset_urls_carry_content_hash(client):
    for path in ("/", "/metodologi"):
        html = client.get(path).text
        assert "?v=ASSET" not in html
        assert f"/static/app.css?v={main.ASSET_V}" in html
    assert re.fullmatch(r"[0-9a-f]{10}", main.ASSET_V)


def test_methodology_matches_scoring(client):
    html = client.get("/metodologi").text
    for key, (_label, weight) in scanner.CHECKS.items():
        assert f'data-weight="{key}">{weight}<' in html
    assert re.search(rf"data-cert-classical>{scanner.CLASSICAL_CERT_PCT}<", html)
    cert_w = scanner.CHECKS["cert"][1]
    total = sum(w for _l, w in scanner.CHECKS.values())
    best = round((total - cert_w + cert_w * scanner.CLASSICAL_CERT_PCT / 100) / total * 100)
    assert f"situs publik hari ini adalah {best}" in html


def test_scan_validates_input(client):
    assert client.post("/api/scan", json={"targets": []}).status_code == 400
    assert client.post("/api/scan", json={"targets": ["a.test", "b.test", "c.test", "d.test", "e.test"]}).status_code == 400
    assert client.post("/api/scan", json={"targets": ["a.test"], "checks": ["nope"]}).status_code == 400


def test_scan_password(client, monkeypatch):
    monkeypatch.setattr(main, "PASSWORD", "s3cret")
    monkeypatch.setattr(main, "_bad", main.defaultdict(main.deque))
    assert client.post("/api/scan", json={"targets": ["a.test"]}).status_code == 401
    def unresolvable(host):
        raise scanner.TargetError("domain tidak dapat di-resolve")
    monkeypatch.setattr(scanner, "resolve_public", unresolvable)
    r = client.post("/api/scan", json={"targets": ["a.test"]}, headers={"X-Scan-Password": "s3cret"})
    assert r.status_code == 200
    assert client.get(f"/api/report/{r.json()['id']}.pdf").headers["content-type"] == "application/pdf"


def test_unknown_report_is_404(client):
    assert client.get("/api/report/deadbeef.pdf").status_code == 404
