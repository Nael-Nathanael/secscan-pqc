"""Minimal raw TLS ClientHello prober.

Sends hand-built ClientHellos and reads only the ServerHello / alert, so we can
ask a server "do you speak TLS 1.3?" or "do you accept group X25519MLKEM768?"
without needing a TLS library that implements the PQ group itself.

Group probe trick: offer exactly one group in supported_groups with an *empty*
key_share. A TLS 1.3 server that supports the group must answer with a
HelloRetryRequest naming it; one that doesn't answers with an alert.
"""

import os
import socket
import ssl
import struct

HRR_RANDOM = bytes.fromhex("CF21AD74E59A6111BE1D8C021E65B891C2A211167ABB8C5E079E09E2C8A8339C")

TLS13_CIPHERS = [0x1301, 0x1302, 0x1303]
TLS12_CIPHERS = [
    0xC02B, 0xC02F, 0xC02C, 0xC030, 0xCCA9, 0xCCA8,
    0xC009, 0xC013, 0xC00A, 0xC014, 0x009C, 0x009D, 0x002F, 0x0035, 0x000A,
]
SIG_ALGS = [
    0x0403, 0x0503, 0x0603, 0x0804, 0x0805, 0x0806, 0x0401, 0x0501, 0x0601,
    0x0807, 0x0808, 0x0203, 0x0201,
    0x0904, 0x0905, 0x0906,  # ML-DSA-44/65/87
]
CLASSIC_GROUPS = [0x001D, 0x0017, 0x0018, 0x0019]

# Display name -> codepoint. Order = order shown in the report.
PQ_GROUPS = [
    ("X25519MLKEM768", 0x11EC, "hybrid"),
    ("SecP256r1MLKEM768", 0x11EB, "hybrid"),
    ("SecP384r1MLKEM1024", 0x11ED, "hybrid"),
    ("MLKEM768", 0x0201, "pure"),
    ("MLKEM1024", 0x0202, "pure"),
    ("X25519Kyber768Draft00", 0x6399, "draft"),
    ("X25519", 0x001D, "classic"),
]

VERSION_NAMES = {0x0304: "1.3", 0x0303: "1.2", 0x0302: "1.1", 0x0301: "1.0"}


def _u16(v):
    return struct.pack(">H", v)


def _vec8(b):
    return bytes([len(b)]) + b


def _vec16(b):
    return _u16(len(b)) + b


def _ext(t, data):
    return _u16(t) + _vec16(data)


def _is_ip(host):
    try:
        socket.inet_pton(socket.AF_INET, host)
        return True
    except OSError:
        pass
    try:
        socket.inet_pton(socket.AF_INET6, host)
        return True
    except OSError:
        return False


def build_client_hello(sni, legacy_version=0x0303, versions=None, groups=None,
                       key_share=None, ciphers=None):
    """versions=None -> no supported_versions ext (pre-1.3 style hello)."""
    groups = groups or CLASSIC_GROUPS
    ciphers = ciphers or TLS12_CIPHERS
    exts = b""
    if sni and not _is_ip(sni):
        name = sni.encode("idna")
        exts += _ext(0x0000, _vec16(b"\x00" + _vec16(name)))
    exts += _ext(0x000A, _vec16(b"".join(_u16(g) for g in groups)))
    exts += _ext(0x000B, _vec8(b"\x00"))
    exts += _ext(0x000D, _vec16(b"".join(_u16(s) for s in SIG_ALGS)))
    exts += _ext(0xFF01, b"\x00")
    if versions:
        exts += _ext(0x002B, _vec8(b"".join(_u16(v) for v in versions)))
        exts += _ext(0x002D, _vec8(b"\x01"))
        shares = b""
        for g, key in (key_share or []):
            shares += _u16(g) + _vec16(key)
        exts += _ext(0x0033, _vec16(shares))
    body = (
        _u16(legacy_version)
        + os.urandom(32)
        + _vec8(os.urandom(32))
        + _vec16(b"".join(_u16(c) for c in ciphers))
        + _vec8(b"\x00")
        + _vec16(exts)
    )
    hs = b"\x01" + len(body).to_bytes(3, "big") + body
    return b"\x16\x03\x01" + _u16(len(hs)) + hs


def _recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("closed")
        buf += chunk
    return buf


def _read_server_hello(sock):
    """Return ("hello", parsed) | ("alert", desc) | ("closed", None)."""
    hs = b""
    for _ in range(16):
        try:
            hdr = _recv_exact(sock, 5)
        except ConnectionError:
            return "closed", None
        ctype, _ver, length = hdr[0], hdr[1:3], struct.unpack(">H", hdr[3:5])[0]
        payload = _recv_exact(sock, length)
        if ctype == 21:
            return "alert", payload[1] if len(payload) > 1 else None
        if ctype != 22:
            return "closed", None
        hs += payload
        if len(hs) >= 4:
            mlen = int.from_bytes(hs[1:4], "big")
            if hs[0] != 2:
                return "closed", None
            if len(hs) >= 4 + mlen:
                return "hello", _parse_server_hello(hs[4:4 + mlen])
    return "closed", None


def _parse_server_hello(b):
    legacy = struct.unpack(">H", b[0:2])[0]
    random = b[2:34]
    sid_len = b[34]
    p = 35 + sid_len
    cipher = struct.unpack(">H", b[p:p + 2])[0]
    p += 3
    exts = {}
    if p + 2 <= len(b):
        end = p + 2 + struct.unpack(">H", b[p:p + 2])[0]
        p += 2
        while p + 4 <= end:
            t, ln = struct.unpack(">HH", b[p:p + 4])
            exts[t] = b[p + 4:p + 4 + ln]
            p += 4 + ln
    version = legacy
    if 0x002B in exts and len(exts[0x002B]) >= 2:
        version = struct.unpack(">H", exts[0x002B][:2])[0]
    group = None
    if 0x0033 in exts and len(exts[0x0033]) >= 2:
        group = struct.unpack(">H", exts[0x0033][:2])[0]
    return {"version": version, "cipher": cipher, "hrr": random == HRR_RANDOM, "group": group}


def _exchange(ip, port, hello, timeout):
    with socket.create_connection((ip, port), timeout=timeout) as s:
        s.settimeout(timeout)
        s.sendall(hello)
        return _read_server_hello(s)


def probe_version(ip, port, sni, version, timeout=6.0):
    """True/False, or None if the port can't be reached at all."""
    try:
        if version == 0x0304:
            hello = build_client_hello(
                sni, versions=[0x0304], groups=CLASSIC_GROUPS,
                key_share=[(0x001D, os.urandom(32))],
                ciphers=TLS13_CIPHERS + TLS12_CIPHERS,
            )
        else:
            hello = build_client_hello(sni, legacy_version=version)
        kind, res = _exchange(ip, port, hello, timeout)
    except (OSError, ConnectionError):
        return None
    except Exception:
        return False
    return kind == "hello" and res["version"] == version


def probe_group(ip, port, sni, group, timeout=6.0):
    try:
        hello = build_client_hello(
            sni, versions=[0x0304], groups=[group], key_share=[], ciphers=TLS13_CIPHERS,
        )
        kind, res = _exchange(ip, port, hello, timeout)
    except (OSError, ConnectionError):
        return None
    except Exception:
        return False
    return kind == "hello" and res["version"] == 0x0304 and res["group"] == group


def fetch_certificate(ip, port, sni, timeout=8.0):
    """Return (der_bytes, trusted: bool, verify_error: str|None)."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    server_name = None if _is_ip(sni) else sni
    with socket.create_connection((ip, port), timeout=timeout) as raw:
        with ctx.wrap_socket(raw, server_hostname=server_name) as s:
            der = s.getpeercert(binary_form=True)

    trusted, err = False, None
    vctx = ssl.create_default_context()
    if server_name is None:
        vctx.check_hostname = False
    try:
        with socket.create_connection((ip, port), timeout=timeout) as raw:
            with vctx.wrap_socket(raw, server_hostname=server_name):
                trusted = True
    except ssl.SSLCertVerificationError as e:
        err = e.verify_message or str(e)
    except (OSError, ssl.SSLError) as e:
        err = str(e)
    return der, trusted, err
