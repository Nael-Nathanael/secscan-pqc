"""Target parsing, probing orchestration, scoring and findings."""

import ipaddress
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import dsa, ec, ed448, ed25519, rsa

import sshprobe
import tlsprobe

WIB = timezone(timedelta(hours=7), "WIB")

CHECKS = {
    "cert": ("Sertifikat", 60),
    "kex": ("Kex PQ", 100),
    "tls": ("TLS", 40),
    "ssh": ("SSH", 50),
}
SSH_PORTS = (22, 2222)
# Any trusted classical key (RSA >= 2048, ECC >= 256, EdDSA): Shor breaks them all alike.
CLASSICAL_CERT_PCT = 65
# What full marks looks like, per check (the "nilai rujukan" on the result sheet).
REFERENCE = {
    "kex": "ML-KEM standar, mis. X25519MLKEM768",
    "cert": "ML-DSA atau SLH-DSA",
    "tls": "TLS 1.3 saja",
    "ssh": "tertutup, atau mlkem768x25519 + ed25519 tanpa RSA",
}


def _key_short(info):
    names = {"rsa": "RSA", "ecc": "ECDSA", "dsa": "DSA"}
    if info["key_type"] in names and info["key_bits"]:
        return f"{names[info['key_type']]} {info['key_bits']}-bit"
    return info["key_label"]

PQ_SIG_OIDS = {
    "2.16.840.1.101.3.4.3.17": "ML-DSA-44",
    "2.16.840.1.101.3.4.3.18": "ML-DSA-65",
    "2.16.840.1.101.3.4.3.19": "ML-DSA-87",
    **{f"2.16.840.1.101.3.4.3.{n}": "SLH-DSA" for n in range(20, 32)},
}

OID_SHORT = {
    "countryName": "C", "organizationName": "O", "organizationalUnitName": "OU",
    "commonName": "CN", "localityName": "L", "stateOrProvinceName": "ST",
}


class TargetError(ValueError):
    pass


def parse_target(raw):
    raw = raw.strip()
    if not raw:
        raise TargetError("kosong")
    if "://" not in raw:
        raw = "//" + raw
    u = urlsplit(raw)
    host = (u.hostname or "").strip(".").lower()
    if not host or len(host) > 253:
        raise TargetError("host tidak valid")
    try:
        port = u.port or 443
    except ValueError:
        raise TargetError("port tidak valid") from None
    return host, port


def resolve_public(host):
    """Resolve and refuse anything that isn't a public address (SSRF guard)."""
    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise TargetError("domain tidak dapat di-resolve") from None
    addrs = []
    for fam, *_rest, sa in infos:
        ip = ipaddress.ip_address(sa[0])
        if not ip.is_global:
            raise TargetError("alamat privat/internal tidak diizinkan")
        addrs.append((fam, str(ip)))
    v4 = [a for f, a in addrs if f == socket.AF_INET]
    return v4[0] if v4 else addrs[0][1]


def _dn(name):
    parts = []
    for attr in name:
        key = OID_SHORT.get(attr.oid._name, attr.oid.dotted_string)
        parts.append(f"{key} = {attr.value}")
    return ", ".join(parts) or "-"


def describe_cert(der):
    cert = x509.load_der_x509_certificate(der)
    info = {
        "subject": _dn(cert.subject),
        "issuer": _dn(cert.issuer),
        "not_after": cert.not_valid_after_utc,
        "sig_alg": None,
        "key_type": None,
        "key_bits": None,
        "key_label": None,
    }
    sig_oid = cert.signature_algorithm_oid.dotted_string
    info["sig_alg"] = PQ_SIG_OIDS.get(sig_oid) or cert.signature_algorithm_oid._name
    pk_oid = cert.public_key_algorithm_oid.dotted_string
    if pk_oid in PQ_SIG_OIDS:
        info["key_type"] = "pq"
        info["key_label"] = PQ_SIG_OIDS[pk_oid]
        return info
    try:
        pk = cert.public_key()
    except Exception:
        info["key_type"] = "unknown"
        info["key_label"] = pk_oid
        return info
    if isinstance(pk, rsa.RSAPublicKey):
        info.update(key_type="rsa", key_bits=pk.key_size, key_label=f"rsaEncryption {pk.key_size} bit")
    elif isinstance(pk, ec.EllipticCurvePublicKey):
        info.update(key_type="ecc", key_bits=pk.key_size, key_label=f"id-ecPublicKey {pk.key_size} bit")
    elif isinstance(pk, (ed25519.Ed25519PublicKey, ed448.Ed448PublicKey)):
        name = "Ed25519" if isinstance(pk, ed25519.Ed25519PublicKey) else "Ed448"
        info.update(key_type="ecc", key_label=name)
    elif isinstance(pk, dsa.DSAPublicKey):
        info.update(key_type="dsa", key_bits=pk.key_size, key_label=f"DSA {pk.key_size} bit")
    else:
        info.update(key_type="unknown", key_label=pk_oid)
    return info


def _run_probes(ip, port, sni, checks):
    jobs = {}
    with ThreadPoolExecutor(max_workers=10) as pool:
        if "cert" in checks:
            jobs["cert"] = pool.submit(tlsprobe.fetch_certificate, ip, port, sni)
        if "tls" in checks or "kex" in checks:
            for code in tlsprobe.VERSION_NAMES:
                jobs[f"v{code}"] = pool.submit(tlsprobe.probe_version, ip, port, sni, code)
        if "kex" in checks:
            for name, code, _kind in tlsprobe.PQ_GROUPS:
                jobs[f"g{name}"] = pool.submit(tlsprobe.probe_group, ip, port, sni, code)
        if "ssh" in checks:
            for p in SSH_PORTS:
                jobs[f"ssh{p}"] = pool.submit(sshprobe.probe_ssh, ip, p)
        out = {}
        for k, f in jobs.items():
            try:
                out[k] = f.result()
            except Exception as e:
                out[k] = e
    return out


def _finding(findings, level, title, text):
    findings.append({"level": level, "title": title, "text": text})


def grade_for(score):
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 65:
        return "C"
    if score >= 50:
        return "D"
    return "E"


def scan_target(raw, checks):
    started = time.monotonic()
    scanned_at = datetime.now(WIB)
    result = {"target": raw.strip(), "scanned_at": scanned_at.isoformat(), "checks": list(checks)}
    try:
        host, port = parse_target(raw)
        result["host"], result["port"] = host, port
        ip = resolve_public(host)
        result["ip"] = ip
    except TargetError as e:
        result["error"] = str(e)
        result["duration"] = round(time.monotonic() - started, 1)
        return result

    pr = _run_probes(ip, port, host, checks)
    components, details, findings = [], [], []
    tls_reachable = any(pr.get(f"v{c}") is not None for c in tlsprobe.VERSION_NAMES) or isinstance(pr.get("cert"), tuple)
    if {"cert", "kex", "tls"} & set(checks) and not tls_reachable:
        result["error"] = f"port {port} tidak merespons (host mati, atau memblokir pemindai)"
        result["duration"] = round(time.monotonic() - started, 1)
        return result

    # --- certificate -------------------------------------------------------
    if "cert" in checks:
        pct = 0
        c = pr.get("cert")
        info = None
        res = "tidak terbaca"
        if isinstance(c, tuple):
            der, trusted, verr = c
            try:
                info = describe_cert(der)
            except ValueError as e:
                res = "tidak valid"
                details.append(("Sertifikat", f"tidak dapat diurai ({e})"))
                _finding(findings, "crit", "Sertifikat tidak valid",
                         "Sertifikat tidak sesuai standar X.509 dan ditolak klien modern. Terbitkan ulang dari CA.")
        else:
            details.append(("Sertifikat", "tidak dapat diambil (TLS tidak merespons)"))
            _finding(findings, "crit", "Sertifikat tidak terbaca", "Server tidak menyelesaikan handshake TLS pada port ini.")
        if info:
            res = _key_short(info)
            exp = info["not_after"]
            details += [
                ("Sertifikat", info["subject"]),
                ("Penerbit", info["issuer"]),
                ("Kunci", f"{info['key_label']} | tanda tangan {info['sig_alg']} | berlaku s/d "
                          f"{exp.strftime('%b %d %H:%M:%S %Y')} GMT"),
                ("Validasi rantai", "tepercaya" if trusted else f"TIDAK tepercaya ({verr})"),
            ]
            kt, bits = info["key_type"], info["key_bits"] or 0
            if kt == "pq":
                pct = 100
                _finding(findings, "good", f"Sertifikat PQC ({info['key_label']})",
                         "Kunci dan tanda tangan sertifikat sudah memakai algoritma tahan kuantum (FIPS 204/205).")
            elif kt == "rsa" and bits < 2048 or kt == "ecc" and 0 < bits < 256:
                pct = 20
                _finding(findings, "crit", f"Kunci sertifikat terlalu kecil ({info['key_label']})",
                         "Sudah lemah terhadap komputer klasik; terbitkan ulang dengan ECDSA P-256 atau RSA-2048+ "
                         "sambil menyiapkan ML-DSA.")
            elif kt in ("rsa", "ecc"):
                pct = CLASSICAL_CERT_PCT
                _finding(findings, "high", f"Sertifikat klasik ({info['key_label']})",
                         "RSA dan ECC sama-sama dipecahkan algoritma Shor; memperbesar kunci RSA tidak menolong. "
                         "Siapkan migrasi ke ML-DSA (FIPS 204) atau sertifikat hybrid begitu CA menerbitkannya.")
            else:
                pct = 20
                _finding(findings, "crit", "Algoritma kunci sertifikat lemah/tidak dikenal",
                         "Ganti dengan ECDSA/RSA modern sambil menyiapkan ML-DSA.")
            if exp < datetime.now(timezone.utc):
                pct = 0
                res += ", kedaluwarsa"
                _finding(findings, "crit", "Sertifikat kedaluwarsa", "Perbarui sertifikat segera.")
            elif not trusted:
                pct = max(0, pct - 30)
                res += ", rantai tidak tepercaya"
                _finding(findings, "crit", "Rantai sertifikat tidak tepercaya",
                         f"Validasi gagal: {verr}. Pasang sertifikat dari CA tepercaya beserta intermediate-nya.")
        components.append(("cert", pct, res))

    # --- PQ key exchange ---------------------------------------------------
    if "kex" in checks:
        support = {name: pr.get(f"g{name}") for name, _c, _k in tlsprobe.PQ_GROUPS}
        kinds = {name: kind for name, _c, kind in tlsprobe.PQ_GROUPS}
        parts = [f"{n} (didukung)" if ok else n for n, ok in support.items()]
        details.append(("Key exchange PQ", ", ".join(parts)))
        std = [n for n, ok in support.items() if ok and kinds[n] in ("hybrid", "pure")]
        draft = support.get("X25519Kyber768Draft00")
        if std:
            pct = 100
            _finding(findings, "good", f"KEX PQ standar ({'/'.join(std)})",
                     "Server menerima key exchange ML-KEM (FIPS 203) di TLS 1.3 — SIAP PQC untuk kerahasiaan sesi.")
        elif draft:
            pct = 50
            _finding(findings, "high", "Hanya Kyber draft",
                     "X25519Kyber768Draft00 sudah usang; aktifkan X25519MLKEM768 (codepoint final).")
        else:
            pct = 0
            _finding(findings, "crit", "TANPA key exchange PQ di TLS 1.3",
                     "Lalu lintas rentan harvest-now-decrypt-later — aktifkan X25519MLKEM768 "
                     "(OpenSSL 3.5+, BoringSSL, Go 1.24+).")
        if not tls_reachable:
            pct = 0
        res = ", ".join(std) if std else "hanya Kyber draft" if draft else "tidak ada grup PQ"
        components.append(("kex", pct, res))

    # --- TLS versions --------------------------------------------------------
    versions = {tlsprobe.VERSION_NAMES[c]: pr.get(f"v{c}") for c in tlsprobe.VERSION_NAMES}
    if "tls" in checks:
        active = [v for v in ("1.0", "1.1", "1.2", "1.3") if versions.get(v)]
        details.append(("TLS version", ", ".join(active) if active else "tidak ada / port tidak merespons"))
        pts = 0
        if versions.get("1.3"):
            pts = 25
            if not versions.get("1.2"):
                pts += 15
        else:
            _finding(findings, "crit", "TLS 1.3 TIDAK aktif", "Tanpa TLS 1.3 tidak ada KEX PQ standar.")
        if versions.get("1.2"):
            _finding(findings, "info", "TLS 1.2 masih aktif",
                     "Pertahankan hanya untuk kompatibilitas klien lama; matikan setelah migrasi.")
        old = [v for v in ("1.0", "1.1") if versions.get(v)]
        if old:
            pts = max(0, pts - 10)
            _finding(findings, "crit", f"TLS {'/'.join(old)} aktif",
                     "Protokol usang (RFC 8996); nonaktifkan segera.")
        components.append(("tls", round(pts / 40 * 100), "TLS " + ", ".join(active) if active else "tidak merespons"))

    # --- SSH -----------------------------------------------------------------
    if "ssh" in checks:
        ssh = next((pr.get(f"ssh{p}") for p in SSH_PORTS
                    if isinstance(pr.get(f"ssh{p}"), dict) and "kex" in pr.get(f"ssh{p}")), None)
        open_any = [p for p in SSH_PORTS if isinstance(pr.get(f"ssh{p}"), dict)]
        if ssh is None:
            if open_any:
                details.append(("SSH", f"port {', '.join(map(str, open_any))} terbuka; KEXINIT tidak terbaca"))
                pct = 50
                res = "terbuka, KEXINIT tak terbaca"
            else:
                details.append(("SSH", f"tertutup pada port {', '.join(map(str, SSH_PORTS))}"))
                pct = 100
                res = "tertutup"
                _finding(findings, "info", "SSH tertutup",
                         f"Tidak ada permukaan SSH publik pada port {', '.join(map(str, SSH_PORTS))}.")
        else:
            hk = ssh["hostkeys"]
            has_rsa = any(k in ("ssh-rsa", "rsa-sha2-256", "rsa-sha2-512") for k in hk)
            has_ed = "ssh-ed25519" in hk
            shown = []
            for k in hk:
                k = "ssh-rsa" if k.startswith("rsa-sha2") else k
                if k not in shown:
                    shown.append(k)
            pq = sorted({sshprobe.PQ_KEX[k] for k in ssh["kex"] if k in sshprobe.PQ_KEX})
            kex_txt = "; ".join(f"{n}: {'ya' if n in pq else 'tidak'}" for n in ("mlkem768x25519", "sntrup761x25519"))
            details.append(("SSH", f"port {ssh['port']} terbuka ({ssh['banner'][8:]}); host keys "
                                   f"{', '.join(shown)}; kex PQ {kex_txt}"))
            pts = (25 if pq else 0) + (15 if has_ed else 0) + (0 if has_rsa else 10)
            pct = round(pts / 50 * 100)
            kinds = dict.fromkeys("RSA" if k == "ssh-rsa" else "ECDSA" if k.startswith("ecdsa") else
                                  "ed25519" if k == "ssh-ed25519" else k for k in shown)
            res = f"port {ssh['port']}, {'/'.join(pq) or 'tanpa KEX PQ'}, host key {' + '.join(kinds)}"
            if has_ed:
                _finding(findings, "good", "SSH host key ed25519", "Baik; tetap siapkan transisi ke tanda tangan PQ.")
            if has_rsa:
                _finding(findings, "high", "SSH host key RSA", "Hapus host key RSA, gunakan ed25519; RSA rentan Shor.")
            if "mlkem768x25519" in pq:
                _finding(findings, "good", "SSH PQ KEX (mlkem768x25519-sha256)", "Server SSH sudah mendukung ML-KEM hybrid.")
            elif pq:
                _finding(findings, "info", "SSH PQ KEX sntrup761",
                         "Sudah tahan kuantum; tambahkan mlkem768x25519-sha256 (OpenSSH >= 9.9).")
            else:
                _finding(findings, "crit", "SSH tanpa PQ KEX", "Perbarui OpenSSH server >= 9.9 untuk mlkem768x25519-sha256.")
        components.append(("ssh", pct, res))

    total_w = sum(CHECKS[k][1] for k, *_ in components)
    score = round(sum(CHECKS[k][1] * p / 100 for k, p, _ in components) / total_w * 100) if total_w else 0
    order = {"crit": 0, "high": 1, "info": 2, "good": 3}
    findings.sort(key=lambda f: order[f["level"]])

    result.update(
        score=score,
        grade=grade_for(score),
        components=[{"key": k, "label": CHECKS[k][0], "max": CHECKS[k][1], "pct": p, "result": r, "ref": REFERENCE[k]}
                    for k, p, r in components],
        details=details,
        findings=findings,
        pqc_status=_pqc_status({k: p for k, p, _ in components}),
        duration=round(time.monotonic() - started, 1),
    )
    return result


def _pqc_status(components):
    d = dict(components)
    if d.get("kex") == 100:
        return "SIAP PQC" if d.get("cert", 0) == 100 else "SEBAGIAN"
    if "kex" not in d:
        return "-"
    return "BELUM SIAP"


def summarize(results):
    ok = [r for r in results if "score" in r]
    grades = {g: sum(1 for r in ok if r["grade"] == g) for g in "ABCDE"}
    avg = round(sum(r["score"] for r in ok) / len(ok)) if ok else 0
    return {"avg": avg, "grades": grades, "hosts": len(results)}
