"""User-facing strings from the scanner, API and PDF, in Bahasa Indonesia (default) and English."""

LANGS = ("id", "en")

MSG = {
    # Target errors
    "err_empty": ("kosong", "empty"),
    "err_host": ("host tidak valid", "invalid host"),
    "err_port": ("port tidak valid", "invalid port"),
    "err_dns": ("domain tidak dapat di-resolve", "the domain does not resolve"),
    "err_private": ("alamat privat/internal tidak diizinkan", "private or internal addresses are not allowed"),
    "err_no_tls": ("port {port} tidak merespons (host mati, atau memblokir pemindai)",
                   "port {port} does not respond (the host is down, or blocks the scanner)"),
    # Reference values
    "ref_kex": ("ML-KEM standar, mis. X25519MLKEM768", "standard ML-KEM, e.g. X25519MLKEM768"),
    "ref_cert": ("ML-DSA atau SLH-DSA", "ML-DSA or SLH-DSA"),
    "ref_tls": ("TLS 1.3 saja", "TLS 1.3 only"),
    "ref_ssh": ("tertutup, atau mlkem768x25519 + ed25519 tanpa RSA", "closed, or mlkem768x25519 + ed25519 without RSA"),
    # Detail labels
    "d_cert": ("Sertifikat", "Certificate"),
    "d_issuer": ("Penerbit", "Issuer"),
    "d_key": ("Kunci", "Key"),
    "d_chain": ("Validasi rantai", "Chain validation"),
    "d_kex": ("Key exchange PQ", "PQ key exchange"),
    "d_tls": ("Versi TLS", "TLS versions"),
    "d_ssh": ("SSH", "SSH"),
    # Detail values
    "dv_unparsable": ("tidak dapat diurai ({e})", "cannot be parsed ({e})"),
    "dv_no_cert": ("tidak dapat diambil (TLS tidak merespons)", "could not be fetched (TLS did not respond)"),
    "dv_key": ("{label} | tanda tangan {sig} | berlaku s/d {exp} GMT", "{label} | signature {sig} | valid until {exp} GMT"),
    "dv_trusted": ("tepercaya", "trusted"),
    "dv_untrusted": ("TIDAK tepercaya ({err})", "NOT trusted ({err})"),
    "dv_supported": ("{name} (didukung)", "{name} (supported)"),
    "dv_no_tls": ("tidak ada / port tidak merespons", "none / port does not respond"),
    "dv_ssh_unreadable": ("port {ports} terbuka; KEXINIT tidak terbaca", "port {ports} open; KEXINIT unreadable"),
    "dv_ssh_closed": ("tertutup pada port {ports}", "closed on ports {ports}"),
    "dv_ssh_open": ("port {port} terbuka ({banner}); host keys {keys}; kex PQ {kex}",
                    "port {port} open ({banner}); host keys {keys}; PQ kex {kex}"),
    "yes": ("ya", "yes"),
    "no": ("tidak", "no"),
    # Short results (the sheet's "Hasil" column)
    "r_unread": ("tidak terbaca", "unreadable"),
    "r_invalid": ("tidak valid", "invalid"),
    "r_expired": (", kedaluwarsa", ", expired"),
    "r_untrusted": (", rantai tidak tepercaya", ", untrusted chain"),
    "r_kyber_only": ("hanya Kyber draft", "Kyber draft only"),
    "r_no_pq": ("tidak ada grup PQ", "no PQ group"),
    "r_no_response": ("tidak merespons", "no response"),
    "r_ssh_unreadable": ("terbuka, KEXINIT tak terbaca", "open, KEXINIT unreadable"),
    "r_ssh_closed": ("tertutup", "closed"),
    "r_ssh_no_pq": ("tanpa KEX PQ", "no PQ KEX"),
    # Findings: (title, text) pairs
    "f_cert_invalid": (("Sertifikat tidak valid",
                        "Sertifikat tidak sesuai standar X.509 dan ditolak klien modern. Terbitkan ulang dari CA."),
                       ("Invalid certificate",
                        "The certificate does not follow X.509 and modern clients reject it. Reissue it from your CA.")),
    "f_cert_unread": (("Sertifikat tidak terbaca", "Server tidak menyelesaikan handshake TLS pada port ini."),
                      ("Certificate unreadable", "The server did not complete a TLS handshake on this port.")),
    "f_cert_pq": (("Sertifikat PQC ({label})",
                   "Kunci dan tanda tangan sertifikat sudah memakai algoritma tahan kuantum (FIPS 204/205)."),
                  ("PQC certificate ({label})",
                   "The certificate's key and signature already use quantum-resistant algorithms (FIPS 204/205).")),
    "f_cert_small": (("Kunci sertifikat terlalu kecil ({label})",
                      "Sudah lemah terhadap komputer klasik; terbitkan ulang dengan ECDSA P-256 atau RSA-2048+ "
                      "sambil menyiapkan ML-DSA."),
                     ("Certificate key too small ({label})",
                      "Already weak against classical computers; reissue with ECDSA P-256 or RSA-2048+ "
                      "while preparing for ML-DSA.")),
    "f_cert_classic": (("Sertifikat klasik ({label})",
                        "RSA dan ECC sama-sama dipecahkan algoritma Shor; memperbesar kunci RSA tidak menolong. "
                        "Siapkan migrasi ke ML-DSA (FIPS 204) atau sertifikat hybrid begitu CA menerbitkannya."),
                       ("Classical certificate ({label})",
                        "Shor's algorithm breaks RSA and ECC alike; a bigger RSA key does not help. "
                        "Prepare to move to ML-DSA (FIPS 204) or a hybrid certificate once CAs issue them.")),
    "f_cert_weak": (("Algoritma kunci sertifikat lemah/tidak dikenal", "Ganti dengan ECDSA/RSA modern sambil menyiapkan ML-DSA."),
                    ("Weak or unknown certificate key algorithm",
                     "Replace it with modern ECDSA/RSA while preparing for ML-DSA.")),
    "f_cert_expired": (("Sertifikat kedaluwarsa", "Perbarui sertifikat segera."),
                       ("Certificate expired", "Renew the certificate now.")),
    "f_chain": (("Rantai sertifikat tidak tepercaya",
                 "Validasi gagal: {err}. Pasang sertifikat dari CA tepercaya beserta intermediate-nya."),
                ("Untrusted certificate chain",
                 "Validation failed: {err}. Install a certificate from a trusted CA with its intermediates.")),
    "f_kex_ok": (("KEX PQ standar ({groups})",
                  "Server menerima key exchange ML-KEM (FIPS 203) di TLS 1.3 — SIAP PQC untuk kerahasiaan sesi."),
                 ("Standard PQ KEX ({groups})",
                  "The server accepts ML-KEM key exchange (FIPS 203) in TLS 1.3, so session secrecy is PQC-ready.")),
    "f_kex_draft": (("Hanya Kyber draft", "X25519Kyber768Draft00 sudah usang; aktifkan X25519MLKEM768 (codepoint final)."),
                    ("Kyber draft only", "X25519Kyber768Draft00 is obsolete; enable X25519MLKEM768 (the final codepoint).")),
    "f_kex_none": (("TANPA key exchange PQ di TLS 1.3",
                    "Lalu lintas rentan harvest-now-decrypt-later — aktifkan X25519MLKEM768 "
                    "(OpenSSL 3.5+, BoringSSL, Go 1.24+)."),
                   ("NO PQ key exchange in TLS 1.3",
                    "Traffic is exposed to harvest-now-decrypt-later; enable X25519MLKEM768 "
                    "(OpenSSL 3.5+, BoringSSL, Go 1.24+).")),
    "f_tls13_off": (("TLS 1.3 TIDAK aktif", "Tanpa TLS 1.3 tidak ada KEX PQ standar."),
                    ("TLS 1.3 NOT enabled", "Without TLS 1.3 there is no standard PQ key exchange.")),
    "f_tls12_on": (("TLS 1.2 masih aktif", "Pertahankan hanya untuk kompatibilitas klien lama; matikan setelah migrasi."),
                   ("TLS 1.2 still enabled", "Keep it only for old clients; turn it off once they have moved.")),
    "f_tls_old": (("TLS {versions} aktif", "Protokol usang (RFC 8996); nonaktifkan segera."),
                  ("TLS {versions} enabled", "Deprecated protocol (RFC 8996); turn it off now.")),
    "f_ssh_closed": (("SSH tertutup", "Tidak ada permukaan SSH publik pada port {ports}."),
                     ("SSH closed", "No public SSH surface on ports {ports}.")),
    "f_ssh_ed": (("SSH host key ed25519", "Baik; tetap siapkan transisi ke tanda tangan PQ."),
                 ("SSH host key ed25519", "Good; still plan the move to PQ signatures.")),
    "f_ssh_rsa": (("SSH host key RSA", "Hapus host key RSA, gunakan ed25519; RSA rentan Shor."),
                  ("SSH host key RSA", "Remove the RSA host key and use ed25519; RSA falls to Shor.")),
    "f_ssh_mlkem": (("SSH PQ KEX (mlkem768x25519-sha256)", "Server SSH sudah mendukung ML-KEM hybrid."),
                    ("SSH PQ KEX (mlkem768x25519-sha256)", "The SSH server already supports hybrid ML-KEM.")),
    "f_ssh_sntrup": (("SSH PQ KEX sntrup761", "Sudah tahan kuantum; tambahkan mlkem768x25519-sha256 (OpenSSH >= 9.9)."),
                     ("SSH PQ KEX sntrup761", "Already quantum-resistant; add mlkem768x25519-sha256 (OpenSSH >= 9.9).")),
    "f_ssh_none": (("SSH tanpa PQ KEX", "Perbarui OpenSSH server >= 9.9 untuk mlkem768x25519-sha256."),
                   ("SSH without PQ KEX", "Upgrade the OpenSSH server to 9.9+ for mlkem768x25519-sha256.")),
    # API
    "api_rate": ("Terlalu banyak scan. Coba lagi beberapa menit lagi.", "Too many scans. Try again in a few minutes."),
    "api_bad_pw_rate": ("Terlalu banyak percobaan password salah. Coba lagi nanti.",
                        "Too many wrong access codes. Try again later."),
    "api_bad_pw": ("Password salah.", "Wrong access code."),
    "api_no_target": ("Masukkan minimal satu domain atau IP.", "Enter at least one domain or IP."),
    "api_too_many": ("Maksimal {n} target per scan.", "At most {n} targets per scan."),
    "api_no_check": ("Pilih minimal satu metode testing.", "Pick at least one check."),
    "api_expired": ("Hasil scan sudah kedaluwarsa, silakan scan ulang.", "This scan has expired; please scan again."),
}


def lang_of(value):
    return value if value in LANGS else "id"


def t(lang, key, **kw):
    text = MSG[key][LANGS.index(lang_of(lang))]
    return text.format(**kw) if kw else text


def finding(lang, key, **kw):
    title, text = MSG[key][LANGS.index(lang_of(lang))]
    return title.format(**kw), text.format(**kw)
