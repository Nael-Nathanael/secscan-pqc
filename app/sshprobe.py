"""Read an SSH server's banner and KEXINIT (sent in cleartext before any crypto)."""

import socket
import struct

PQ_KEX = {
    "mlkem768x25519-sha256": "mlkem768x25519",
    "sntrup761x25519-sha512": "sntrup761x25519",
    "sntrup761x25519-sha512@openssh.com": "sntrup761x25519",
}


def _name_lists(payload, count):
    p, out = 17, []  # 1 byte msg type + 16 byte cookie
    for _ in range(count):
        ln = struct.unpack(">I", payload[p:p + 4])[0]
        out.append([x for x in payload[p + 4:p + 4 + ln].decode("ascii", "replace").split(",") if x])
        p += 4 + ln
    return out


def probe_ssh(ip, port, timeout=6.0):
    """Return None if the port is closed, else a dict (possibly with 'error')."""
    try:
        s = socket.create_connection((ip, port), timeout=timeout)
    except OSError:
        return None
    res = {"port": port}
    try:
        s.settimeout(timeout)
        buf = b""
        banner = None
        while banner is None and len(buf) < 16384:
            chunk = s.recv(4096)
            if not chunk:
                break
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                if line.startswith(b"SSH-"):
                    banner = line.rstrip(b"\r").decode("ascii", "replace")
                    break
        if banner is None:
            res["error"] = "port terbuka, bukan layanan SSH"
            return res
        res["banner"] = banner
        s.sendall(b"SSH-2.0-SecScan_1.0\r\n")
        while len(buf) < 5:
            chunk = s.recv(4096)
            if not chunk:
                raise ConnectionError
            buf += chunk
        plen = struct.unpack(">I", buf[:4])[0]
        if plen > 65536:
            raise ValueError("packet too large")
        while len(buf) < 4 + plen:
            chunk = s.recv(4096)
            if not chunk:
                raise ConnectionError
            buf += chunk
        pad = buf[4]
        payload = buf[5:4 + plen - pad]
        if payload[0] != 20:
            raise ValueError("no KEXINIT")
        kex, hostkeys = _name_lists(payload, 2)
        res["kex"] = kex
        res["hostkeys"] = hostkeys
    except Exception:
        res.setdefault("error", "gagal membaca KEXINIT")
    finally:
        s.close()
    return res
