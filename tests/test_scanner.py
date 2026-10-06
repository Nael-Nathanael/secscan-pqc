from datetime import datetime, timedelta, timezone

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa
from cryptography.x509.oid import NameOID

import i18n
import scanner
import tlsprobe

TLS13, TLS12, TLS10 = 0x0304, 0x0303, 0x0301


def make_cert(key, days=30):
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "example.test")])
    now = datetime.now(timezone.utc)
    algo = None if isinstance(key, ed25519.Ed25519PrivateKey) else hashes.SHA256()
    cert = (
        x509.CertificateBuilder()
        .subject_name(name).issuer_name(name).public_key(key.public_key())
        .serial_number(1).not_valid_before(now - timedelta(days=60))
        .not_valid_after(now + timedelta(days=days))
        .sign(key, algo)
    )
    return cert.public_bytes(serialization.Encoding.DER)


def probes(cert=None, trusted=True, versions=(TLS13,), groups=("X25519MLKEM768", "X25519"), ssh=None):
    out = {f"v{c}": c in versions for c in tlsprobe.VERSION_NAMES}
    out.update({f"g{n}": n in groups for n, _c, _k in tlsprobe.PQ_GROUPS})
    out["cert"] = (cert, trusted, None if trusted else "self-signed") if cert else None
    for p in scanner.SSH_PORTS:
        out[f"ssh{p}"] = ssh if p == 22 else None
    return out


def _tlvs(buf):
    items, i = [], 0
    while i < len(buf):
        n, h = buf[i + 1], 2
        if n & 0x80:
            h += n & 0x7F
            n = int.from_bytes(buf[i + 2:i + h], "big")
        items.append((buf[i], buf[i + h:i + h + n]))
        i += h + n
    return items


def _tlv(tag, body):
    n = len(body)
    size = bytes([n]) if n < 128 else bytes([0x80 | (n.bit_length() + 7) // 8]) + n.to_bytes((n.bit_length() + 7) // 8, "big")
    return bytes([tag]) + size + body


def ecdsa_cert_with_null_params():
    """ECDSA cert whose signature AlgorithmIdentifier carries NULL params, as old Java emitted."""
    plain, null = bytes.fromhex("300a06082a8648ce3d040302"), bytes.fromhex("300c06082a8648ce3d0403020500")
    (_, body), = _tlvs(make_cert(ec.generate_private_key(ec.SECP256R1())))
    (_, tbs), _alg, sig = _tlvs(body)
    tbs = _tlv(0x30, tbs.replace(plain, null, 1))
    return _tlv(0x30, tbs + null + _tlv(*sig))


@pytest.fixture
def scan(monkeypatch):
    def run(checks=tuple(scanner.CHECKS), **kw):
        monkeypatch.setattr(scanner, "resolve_public", lambda host: "203.0.113.10")
        monkeypatch.setattr(scanner, "_run_probes", lambda *a: probes(**kw))
        return scanner.scan_target("example.test", list(checks))
    return run


def pct(result, key):
    return next(c["pct"] for c in result["components"] if c["key"] == key)


@pytest.mark.parametrize("key", [
    rsa.generate_private_key(65537, 2048),
    rsa.generate_private_key(65537, 4096),
    ec.generate_private_key(ec.SECP256R1()),
    ec.generate_private_key(ec.SECP384R1()),
    ed25519.Ed25519PrivateKey.generate(),
], ids=["rsa2048", "rsa4096", "p256", "p384", "ed25519"])
def test_classical_certs_score_alike(scan, key):
    assert pct(scan(["cert"], cert=make_cert(key)), "cert") == scanner.CLASSICAL_CERT_PCT


def test_small_rsa_is_critical(scan):
    r = scan(["cert"], cert=make_cert(rsa.generate_private_key(65537, 1024)))
    assert pct(r, "cert") == 20
    assert r["findings"][0]["level"] == "crit"


def test_expired_cert_scores_zero(scan):
    key = ec.generate_private_key(ec.SECP256R1())
    assert pct(scan(["cert"], cert=make_cert(key, days=-1)), "cert") == 0


def test_untrusted_chain_costs_30(scan):
    key = ec.generate_private_key(ec.SECP256R1())
    assert pct(scan(["cert"], cert=make_cert(key), trusted=False), "cert") == scanner.CLASSICAL_CERT_PCT - 30


def test_malformed_cert_is_critical_not_fatal(scan):
    r = scan(["cert", "tls"], cert=ecdsa_cert_with_null_params())
    assert pct(r, "cert") == 0
    assert r["findings"][0]["level"] == "crit"
    assert pct(r, "tls") == 100


@pytest.mark.parametrize("versions,expected", [
    ((TLS13,), 100),
    ((TLS13, TLS12), 62),
    ((TLS13, TLS12, TLS10), 38),
    ((TLS12,), 0),
])
def test_tls_versions(scan, versions, expected):
    assert pct(scan(["tls"], versions=versions), "tls") == expected


@pytest.mark.parametrize("groups,expected", [
    (("X25519MLKEM768",), 100),
    (("MLKEM1024",), 100),
    (("X25519Kyber768Draft00", "X25519"), 50),
    (("X25519",), 0),
])
def test_pq_key_exchange(scan, groups, expected):
    assert pct(scan(["kex"], groups=groups), "kex") == expected


@pytest.mark.parametrize("ssh,expected", [
    (None, 100),
    ({"port": 22, "banner": "SSH-2.0-OpenSSH_10.0", "kex": ["mlkem768x25519-sha256"], "hostkeys": ["ssh-ed25519"]}, 100),
    ({"port": 22, "banner": "SSH-2.0-OpenSSH_9.6", "kex": ["sntrup761x25519-sha512@openssh.com"],
      "hostkeys": ["rsa-sha2-512", "ssh-ed25519"]}, 80),
    ({"port": 22, "banner": "SSH-2.0-OpenSSH_8.2", "kex": ["curve25519-sha256"], "hostkeys": ["rsa-sha2-512"]}, 0),
])
def test_ssh(scan, ssh, expected):
    assert pct(scan(["ssh"], ssh=ssh), "ssh") == expected


def test_composite_and_status(scan):
    r = scan(cert=make_cert(ec.generate_private_key(ec.SECP256R1())))
    # (60*0.65 + 100 + 40 + 50) / 250
    assert r["score"] == 92
    assert r["grade"] == "A"
    assert r["pqc_status"] == "SEBAGIAN"


def test_sheet_fields(scan):
    ssh = {"port": 22, "banner": "SSH-2.0-OpenSSH_9.6", "kex": ["sntrup761x25519-sha512@openssh.com"],
           "hostkeys": ["rsa-sha2-512", "ecdsa-sha2-nistp256", "ssh-ed25519"]}
    r = scan(cert=make_cert(ec.generate_private_key(ec.SECP256R1())), versions=(TLS13, TLS12), ssh=ssh)
    got = {c["key"]: (c["result"], c["ref"]) for c in r["components"]}
    assert got["cert"][0] == "ECDSA 256-bit"
    assert got["kex"][0] == "X25519MLKEM768"
    assert got["tls"][0] == "TLS 1.2, 1.3"
    assert got["ssh"][0] == "port 22, sntrup761x25519, host key RSA + ECDSA + ed25519"
    assert all(ref == i18n.t("id", f"ref_{k}") for k, (_res, ref) in got.items())


def test_english_output(scan, monkeypatch):
    monkeypatch.setattr(scanner, "resolve_public", lambda host: "203.0.113.10")
    monkeypatch.setattr(scanner, "_run_probes", lambda *a: probes(cert=make_cert(ec.generate_private_key(ec.SECP256R1()))))
    r = scanner.scan_target("example.test", list(scanner.CHECKS), lang="en")
    assert r["score"] == 92
    titles = [f["title"] for f in r["findings"]]
    assert "Classical certificate (id-ecPublicKey 256 bit)" in titles
    assert "SSH closed" in titles
    assert {c["key"]: c["ref"] for c in r["components"]}["tls"] == "TLS 1.3 only"
    assert ("Chain validation", "trusted") in r["details"]


def test_target_errors_are_translated(monkeypatch):
    def nx(host):
        raise scanner.TargetError("err_dns")
    monkeypatch.setattr(scanner, "resolve_public", nx)
    assert scanner.scan_target("nope.invalid", ["kex"], lang="en")["error"] == "the domain does not resolve"
    assert scanner.scan_target("nope.invalid", ["kex"])["error"] == "domain tidak dapat di-resolve"


def test_catalog_complete():
    for key, value in i18n.MSG.items():
        assert len(value) == len(i18n.LANGS), key


@pytest.mark.parametrize("score,grade", [(100, "A"), (90, "A"), (89, "B"), (65, "C"), (50, "D"), (49, "E")])
def test_grade_bands(score, grade):
    assert scanner.grade_for(score) == grade


@pytest.mark.parametrize("raw,expected", [
    ("example.com", ("example.com", 443)),
    ("https://Example.com:8443/path", ("example.com", 8443)),
    ("example.com.", ("example.com", 443)),
])
def test_parse_target(raw, expected):
    assert scanner.parse_target(raw) == expected


@pytest.mark.parametrize("raw", ["", "example.com:99999"])
def test_parse_target_rejects(raw):
    with pytest.raises(scanner.TargetError):
        scanner.parse_target(raw)


@pytest.mark.parametrize("host", ["127.0.0.1", "10.0.0.5", "192.168.1.1", "169.254.169.254", "::1"])
def test_private_addresses_refused(host):
    with pytest.raises(scanner.TargetError):
        scanner.resolve_public(host)


def test_hello_retry_request_is_recognised():
    body = (b"\x03\x03" + tlsprobe.HRR_RANDOM + b"\x00" + b"\x13\x01" + b"\x00"
            + b"\x00\x0c" + b"\x00\x2b\x00\x02\x03\x04" + b"\x00\x33\x00\x02\x11\xec")
    assert tlsprobe._parse_server_hello(body) == {"version": TLS13, "cipher": 0x1301, "hrr": True, "group": 0x11EC}
