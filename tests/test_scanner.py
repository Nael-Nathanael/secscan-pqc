from datetime import datetime, timedelta, timezone

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa
from cryptography.x509.oid import NameOID

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
