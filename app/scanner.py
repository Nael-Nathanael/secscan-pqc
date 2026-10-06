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
from i18n import finding, t

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
    """Carries an i18n message key."""


def parse_target(raw):
    raw = raw.strip()
    if not raw:
        raise TargetError("err_empty")
    if "://" not in raw:
        raw = "//" + raw
    u = urlsplit(raw)
    host = (u.hostname or "").strip(".").lower()
    if not host or len(host) > 253:
        raise TargetError("err_host")
    try:
        port = u.port or 443
    except ValueError:
        raise TargetError("err_port") from None
    return host, port


def resolve_public(host):
    """Resolve and refuse anything that isn't a public address (SSRF guard)."""
    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise TargetError("err_dns") from None
    addrs = []
    for fam, *_rest, sa in infos:
        ip = ipaddress.ip_address(sa[0])
        if not ip.is_global:
            raise TargetError("err_private")
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


def scan_target(raw, checks, lang="id"):
    started = time.monotonic()
    scanned_at = datetime.now(WIB)
    result = {"target": raw.strip(), "scanned_at": scanned_at.isoformat(), "checks": list(checks)}
    findings = []

    def find(level, key, **kw):
        title, text = finding(lang, key, **kw)
        findings.append({"level": level, "title": title, "text": text})

    try:
        host, port = parse_target(raw)
        result["host"], result["port"] = host, port
        ip = resolve_public(host)
        result["ip"] = ip
    except TargetError as e:
        result["error"] = t(lang, str(e))
        result["duration"] = round(time.monotonic() - started, 1)
        return result

    pr = _run_probes(ip, port, host, checks)
    components, details = [], []
    tls_reachable = any(pr.get(f"v{c}") is not None for c in tlsprobe.VERSION_NAMES) or isinstance(pr.get("cert"), tuple)
    if {"cert", "kex", "tls"} & set(checks) and not tls_reachable:
        result["error"] = t(lang, "err_no_tls", port=port)
        result["duration"] = round(time.monotonic() - started, 1)
        return result

    # --- certificate -------------------------------------------------------
    if "cert" in checks:
        pct = 0
        c = pr.get("cert")
        info = None
        res = t(lang, "r_unread")
        if isinstance(c, tuple):
            der, trusted, verr = c
            try:
                info = describe_cert(der)
            except ValueError as e:
                res = t(lang, "r_invalid")
                details.append((t(lang, "d_cert"), t(lang, "dv_unparsable", e=e)))
                find("crit", "f_cert_invalid")
        else:
            details.append((t(lang, "d_cert"), t(lang, "dv_no_cert")))
            find("crit", "f_cert_unread")
        if info:
            res = _key_short(info)
            exp = info["not_after"]
            details += [
                (t(lang, "d_cert"), info["subject"]),
                (t(lang, "d_issuer"), info["issuer"]),
                (t(lang, "d_key"), t(lang, "dv_key", label=info["key_label"], sig=info["sig_alg"],
                                     exp=exp.strftime("%b %d %H:%M:%S %Y"))),
                (t(lang, "d_chain"), t(lang, "dv_trusted") if trusted else t(lang, "dv_untrusted", err=verr)),
            ]
            kt, bits = info["key_type"], info["key_bits"] or 0
            if kt == "pq":
                pct = 100
                find("good", "f_cert_pq", label=info["key_label"])
            elif kt == "rsa" and bits < 2048 or kt == "ecc" and 0 < bits < 256:
                pct = 20
                find("crit", "f_cert_small", label=info["key_label"])
            elif kt in ("rsa", "ecc"):
                pct = CLASSICAL_CERT_PCT
                find("high", "f_cert_classic", label=info["key_label"])
            else:
                pct = 20
                find("crit", "f_cert_weak")
            if exp < datetime.now(timezone.utc):
                pct = 0
                res += t(lang, "r_expired")
                find("crit", "f_cert_expired")
            elif not trusted:
                pct = max(0, pct - 30)
                res += t(lang, "r_untrusted")
                find("crit", "f_chain", err=verr)
        components.append(("cert", pct, res))

    # --- PQ key exchange ---------------------------------------------------
    if "kex" in checks:
        support = {name: pr.get(f"g{name}") for name, _c, _k in tlsprobe.PQ_GROUPS}
        kinds = {name: kind for name, _c, kind in tlsprobe.PQ_GROUPS}
        parts = [t(lang, "dv_supported", name=n) if ok else n for n, ok in support.items()]
        details.append((t(lang, "d_kex"), ", ".join(parts)))
        std = [n for n, ok in support.items() if ok and kinds[n] in ("hybrid", "pure")]
        draft = support.get("X25519Kyber768Draft00")
        if std:
            pct = 100
            find("good", "f_kex_ok", groups="/".join(std))
        elif draft:
            pct = 50
            find("high", "f_kex_draft")
        else:
            pct = 0
            find("crit", "f_kex_none")
        if not tls_reachable:
            pct = 0
        res = ", ".join(std) if std else t(lang, "r_kyber_only") if draft else t(lang, "r_no_pq")
        components.append(("kex", pct, res))

    # --- TLS versions --------------------------------------------------------
    versions = {tlsprobe.VERSION_NAMES[c]: pr.get(f"v{c}") for c in tlsprobe.VERSION_NAMES}
    if "tls" in checks:
        active = [v for v in ("1.0", "1.1", "1.2", "1.3") if versions.get(v)]
        details.append((t(lang, "d_tls"), ", ".join(active) if active else t(lang, "dv_no_tls")))
        pts = 0
        if versions.get("1.3"):
            pts = 25
            if not versions.get("1.2"):
                pts += 15
        else:
            find("crit", "f_tls13_off")
        if versions.get("1.2"):
            find("info", "f_tls12_on")
        old = [v for v in ("1.0", "1.1") if versions.get(v)]
        if old:
            pts = max(0, pts - 10)
            find("crit", "f_tls_old", versions="/".join(old))
        res = "TLS " + ", ".join(active) if active else t(lang, "r_no_response")
        components.append(("tls", round(pts / 40 * 100), res))

    # --- SSH -----------------------------------------------------------------
    if "ssh" in checks:
        ports = ", ".join(map(str, SSH_PORTS))
        ssh = next((pr.get(f"ssh{p}") for p in SSH_PORTS
                    if isinstance(pr.get(f"ssh{p}"), dict) and "kex" in pr.get(f"ssh{p}")), None)
        open_any = [p for p in SSH_PORTS if isinstance(pr.get(f"ssh{p}"), dict)]
        if ssh is None:
            if open_any:
                details.append((t(lang, "d_ssh"), t(lang, "dv_ssh_unreadable", ports=", ".join(map(str, open_any)))))
                pct = 50
                res = t(lang, "r_ssh_unreadable")
            else:
                details.append((t(lang, "d_ssh"), t(lang, "dv_ssh_closed", ports=ports)))
                pct = 100
                res = t(lang, "r_ssh_closed")
                find("info", "f_ssh_closed", ports=ports)
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
            kex_txt = "; ".join(f"{n}: {t(lang, 'yes') if n in pq else t(lang, 'no')}"
                                for n in ("mlkem768x25519", "sntrup761x25519"))
            details.append((t(lang, "d_ssh"), t(lang, "dv_ssh_open", port=ssh["port"], banner=ssh["banner"][8:],
                                                 keys=", ".join(shown), kex=kex_txt)))
            pts = (25 if pq else 0) + (15 if has_ed else 0) + (0 if has_rsa else 10)
            pct = round(pts / 50 * 100)
            kinds = dict.fromkeys("RSA" if k == "ssh-rsa" else "ECDSA" if k.startswith("ecdsa") else
                                  "ed25519" if k == "ssh-ed25519" else k for k in shown)
            res = f"port {ssh['port']}, {'/'.join(pq) or t(lang, 'r_ssh_no_pq')}, host key {' + '.join(kinds)}"
            if has_ed:
                find("good", "f_ssh_ed")
            if has_rsa:
                find("high", "f_ssh_rsa")
            if "mlkem768x25519" in pq:
                find("good", "f_ssh_mlkem")
            elif pq:
                find("info", "f_ssh_sntrup")
            else:
                find("crit", "f_ssh_none")
        components.append(("ssh", pct, res))

    total_w = sum(CHECKS[k][1] for k, *_ in components)
    score = round(sum(CHECKS[k][1] * p / 100 for k, p, _ in components) / total_w * 100) if total_w else 0
    order = {"crit": 0, "high": 1, "info": 2, "good": 3}
    findings.sort(key=lambda f: order[f["level"]])

    result.update(
        score=score,
        grade=grade_for(score),
        components=[{"key": k, "label": CHECKS[k][0], "max": CHECKS[k][1], "pct": p, "result": r,
                     "ref": t(lang, f"ref_{k}")} for k, p, r in components],
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
