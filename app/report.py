"""PDF report: the web result sheet, one sheet per host."""

import io
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from scanner import WIB

BRAND = os.environ.get("BRAND_NAME", "SecScan PQC")
SITE = os.environ.get("SITE_NAME", "")
MADE_BY = f"{BRAND}, {SITE}" if SITE else BRAND

FONTS = os.path.join(os.path.dirname(__file__), "fonts")
for name, file in [("Sans", "AtkinsonHyperlegibleNext-Regular"), ("Sans-Bold", "AtkinsonHyperlegibleNext-Bold"),
                   ("Mono", "AtkinsonHyperlegibleMono-Regular"), ("Mono-Bold", "AtkinsonHyperlegibleMono-Bold")]:
    pdfmetrics.registerFont(TTFont(name, os.path.join(FONTS, f"{file}.ttf")))

INK = colors.HexColor("#1d2321")
MUTED = colors.HexColor("#56615d")
RULE = colors.HexColor("#c9d1ce")
RULE_SOFT = colors.HexColor("#e3e8e6")
TEAL = colors.HexColor("#00705f")
RED = colors.HexColor("#c0262b")

ORDER = ["kex", "cert", "ssh", "tls"]
LEVEL_COLOR = {"crit": RED, "high": RED, "info": MUTED, "good": TEAL}

TX = {
    "id": {
        "names": {"kex": "Key exchange PQ", "cert": "Sertifikat", "ssh": "SSH", "tls": "Versi TLS"},
        "levels": {"crit": "KRITIS", "high": "PERHATIAN", "info": "CATATAN", "good": "BAIK"},
        "status": {"SIAP PQC": "siap PQC", "SEBAGIAN": "sebagian siap", "BELUM SIAP": "belum siap"},
        "by": "oleh MiraeStudio.id", "title": "HASIL PEMERIKSAAN KESIAPAN PQC", "sub": "Diperiksa dari luar, read-only",
        "patient": ("Host", "Alamat IP", "Waktu pemeriksaan"), "results": "HASIL",
        "head": ("Pemeriksaan", "Hasil", "Nilai rujukan", "Nilai", "Flag", "Bobot"),
        "total": "Skor komposit, status {status}",
        "legend": "Nilai 0–100 per pemeriksaan. L: di bawah nilai rujukan. !: kritis. "
                  "Skor komposit = rata-rata tertimbang dengan bobot.",
        "conclusion": "KESIMPULAN", "tech": "RINCIAN TEKNIS", "refs_label": "Rujukan",
        "refs": "NIST FIPS 203 (ML-KEM), FIPS 204 (ML-DSA), FIPS 205 (SLH-DSA), NIST IR 8547; RFC 10024 (hybrid ML-KEM "
                "untuk TLS 1.3); RFC 8446; RFC 8996; BSSN, Panduan Migrasi ke Post-Quantum Cryptography v1.0 (2025).",
        "method": "Metode dan nilai rujukan: https://{site}/metodologi",
        "failed": "Tidak dapat diperiksa: {error}.", "cont": "lanjutan",
        "batch_head": ("Host", "Skor", "Grade", "No. lembar"), "batch_fail": "gagal",
        "batch_title": "RINGKASAN PEMERIKSAAN", "batch_sub": "{n} host, rata-rata skor {avg}",
        "footer": "Dibuat oleh {by} · pemeriksaan read-only dari luar", "page": "halaman {n}",
        "doc_title": "Hasil Pemeriksaan Kesiapan PQC",
    },
    "en": {
        "names": {"kex": "PQ key exchange", "cert": "Certificate", "ssh": "SSH", "tls": "TLS versions"},
        "levels": {"crit": "CRITICAL", "high": "ATTENTION", "info": "NOTE", "good": "GOOD"},
        "status": {"SIAP PQC": "PQC-ready", "SEBAGIAN": "partly ready", "BELUM SIAP": "not ready"},
        "by": "by MiraeStudio.id", "title": "PQC READINESS RESULT", "sub": "Checked from outside, read-only",
        "patient": ("Host", "IP address", "Checked at"), "results": "RESULTS",
        "head": ("Check", "Result", "Reference value", "Score", "Flag", "Weight"),
        "total": "Composite score, {status}",
        "legend": "Score 0–100 per check. L: below the reference value. !: critical. "
                  "Composite score = weighted average using the weights.",
        "conclusion": "CONCLUSION", "tech": "TECHNICAL DETAILS", "refs_label": "References",
        "refs": "NIST FIPS 203 (ML-KEM), FIPS 204 (ML-DSA), FIPS 205 (SLH-DSA), NIST IR 8547; RFC 10024 (hybrid ML-KEM "
                "for TLS 1.3); RFC 8446; RFC 8996; BSSN, Post-Quantum Cryptography Migration Guide v1.0 (2025).",
        "method": "Method and reference values: https://{site}/en/methodology",
        "failed": "Could not be checked: {error}.", "cont": "continued",
        "batch_head": ("Host", "Score", "Grade", "Sheet no."), "batch_fail": "failed",
        "batch_title": "SCAN SUMMARY", "batch_sub": "{n} hosts, average score {avg}",
        "footer": "Made by {by} · read-only check from outside", "page": "page {n}",
        "doc_title": "PQC Readiness Result",
    },
}


def _s(name, **kw):
    base = dict(fontName="Sans", fontSize=9, leading=12.5, textColor=INK)
    base.update(kw)
    return ParagraphStyle(name, **base)


S_BRAND = _s("brand", fontName="Sans-Bold", fontSize=12, leading=14)
S_BY = _s("by", fontSize=8, textColor=MUTED)
S_NO = _s("no", fontName="Mono", fontSize=8, leading=11, textColor=MUTED, alignment=TA_RIGHT)
S_TITLE = _s("title", fontName="Sans-Bold", fontSize=10.5, leading=13)
S_SUB = _s("sub", fontSize=8, textColor=MUTED)
S_LABEL = _s("label", fontSize=7.5, leading=9, textColor=MUTED)
S_VALUE = _s("value", fontName="Mono", fontSize=9.5, leading=12)
S_CAP = _s("cap", fontName="Sans-Bold", fontSize=8, leading=10)
S_CELL = _s("cell", fontSize=9, leading=11.5)
S_CELL_MUTED = _s("cellm", fontSize=8.5, leading=11, textColor=MUTED)
S_CELL_MONO = _s("cellmono", fontName="Mono", fontSize=9, leading=11.5)
S_CELL_MONO_B = _s("cellmonob", fontName="Mono-Bold", fontSize=9, leading=11.5)
S_CELL_MONO_OK = _s("cellmonook", fontName="Mono", fontSize=9, leading=11.5, textColor=TEAL)
S_NUM = _s("num", fontName="Mono", fontSize=9, leading=11.5, alignment=TA_RIGHT)
S_TOTAL = _s("total", fontName="Sans-Bold", fontSize=9.5, leading=12, alignment=TA_RIGHT)
S_SCORE = _s("score", fontName="Mono-Bold", fontSize=22, leading=24, alignment=TA_RIGHT)
S_LEGEND = _s("legend", fontSize=7.5, leading=10, textColor=MUTED)
S_FIND = _s("find", fontName="Sans-Bold", fontSize=9, leading=11.5)
S_FIND_TEXT = _s("findt", fontSize=8.5, leading=11, textColor=MUTED)
S_TECH_K = _s("techk", fontSize=8, leading=10.5, textColor=MUTED)
S_TECH_V = _s("techv", fontName="Mono", fontSize=7.5, leading=10)
S_ERR = _s("err", textColor=RED)

WIDTH = A4[0] - 32 * mm


def _esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _letterhead(x, created, no):
    brand = Table([[Paragraph("PQ", _s("code", fontName="Mono-Bold", fontSize=8.5, leading=10)),
                    Paragraph(_esc(BRAND), S_BRAND)]], colWidths=[9 * mm, None])
    brand.setStyle(TableStyle([("BOX", (0, 0), (0, 0), 1.1, INK), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                               ("LEFTPADDING", (0, 0), (0, 0), 2), ("RIGHTPADDING", (0, 0), (0, 0), 2),
                               ("TOPPADDING", (0, 0), (0, 0), 2), ("BOTTOMPADDING", (0, 0), (0, 0), 1)]))
    left = [brand, Spacer(1, 2), Paragraph(x["by"] + (f" · {_esc(SITE)}" if SITE else ""), S_BY)]
    right = Paragraph(f"No. {_esc(no)}<br/>{created.strftime('%d-%m-%Y %H:%M')} WIB", S_NO)
    t = Table([[left, right]], colWidths=[WIDTH * 0.6, WIDTH * 0.4])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                           ("LINEBELOW", (0, 0), (-1, 0), 0.6, RULE)]))
    return t


def _title(x):
    t = Table([[[Paragraph(x["title"], S_TITLE), Paragraph(x["sub"], S_SUB)]]], colWidths=[WIDTH])
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 1.6, INK), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return t


def _patient(x, r, when):
    host = (r.get("host") or r["target"]) + (f":{r['port']}" if r.get("port") and r["port"] != 443 else "")
    cells = list(zip(x["patient"], (host, r.get("ip", "–"), when), strict=True))
    t = Table([[[Paragraph(k, S_LABEL), Paragraph(_esc(v), S_VALUE)] for k, v in cells]], colWidths=[WIDTH / 3] * 3)
    t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 7),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 7), ("LINEBELOW", (0, 0), (-1, -1), 0.6, RULE),
                           ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t


class _Flag(Table):
    def __init__(self, pct):
        if pct >= 100:
            super().__init__([[""]], colWidths=[7 * mm], rowHeights=[5 * mm])
            return
        crit = pct < 50
        style = _s("flag", fontName="Mono-Bold", fontSize=8.5, leading=10, alignment=1,
                   textColor=colors.white if crit else RED)
        super().__init__([[Paragraph("!" if crit else "L", style)]], colWidths=[6 * mm], rowHeights=[5 * mm])
        cmds = [("BOX", (0, 0), (-1, -1), 1, RED), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]
        if crit:
            cmds.append(("BACKGROUND", (0, 0), (-1, -1), RED))
        self.setStyle(TableStyle(cmds))


def _results(x, r):
    comps = [c for k in ORDER for c in r["components"] if c["key"] == k]
    right = _s("hr", fontSize=7.5, leading=9, textColor=MUTED, alignment=TA_RIGHT)
    h = x["head"]
    head = [Paragraph(h[0], S_LABEL), Paragraph(h[1], S_LABEL), Paragraph(h[2], S_LABEL),
            Paragraph(h[3], right), Paragraph(h[4], S_LABEL), Paragraph(h[5], right)]
    rows = [head]
    for c in comps:
        rows.append([Paragraph(x["names"][c["key"]], S_CELL),
                     Paragraph(_esc(c["result"]), S_CELL_MONO_B if c["pct"] < 100 else S_CELL_MONO_OK),
                     Paragraph(_esc(c["ref"]), S_CELL_MUTED),
                     Paragraph(str(c["pct"]), S_NUM), _Flag(c["pct"]), Paragraph(str(c["max"]), S_NUM)])
    status = x["status"].get(r["pqc_status"], r["pqc_status"])
    grade = Table([[Paragraph(r["grade"], _s("g", fontName="Mono-Bold", fontSize=11, leading=12, alignment=1))]],
                  colWidths=[8 * mm], rowHeights=[7 * mm])
    grade.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1.1, INK), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                               ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
    total = Table([[Paragraph(_esc(x["total"].format(status=status)), S_TOTAL),
                    Paragraph(f"{r['score']}<font size=10>/100</font>", S_SCORE), grade]],
                  colWidths=[None, 26 * mm, 11 * mm])
    total.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                               ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("ALIGN", (2, 0), (2, 0), "RIGHT")]))
    rows.append([total, "", "", "", "", ""])
    t = Table(rows, colWidths=[30 * mm, 38 * mm, None, 12 * mm, 11 * mm, 12 * mm], repeatRows=1)
    n = len(rows) - 1
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, 0), 0.9, INK),
        ("LINEBELOW", (0, 1), (-1, n - 1), 0.5, RULE_SOFT),
        ("LINEABOVE", (0, n), (-1, n), 1.6, INK), ("SPAN", (0, n), (-1, n)), ("TOPPADDING", (0, n), (-1, n), 9),
        ("ALIGN", (4, 1), (4, n - 1), "CENTER"), ("RIGHTPADDING", (-1, 0), (-1, -1), 0),
    ]))
    return t


def _conclusion(x, findings):
    rows = [[Paragraph(x["conclusion"], S_CAP), ""]]
    for f in findings:
        label, color = x["levels"][f["level"]], LEVEL_COLOR[f["level"]]
        rows.append([Paragraph(label, _s(f"l{f['level']}", fontName="Mono-Bold", fontSize=7, leading=11, textColor=color)),
                     [Paragraph(_esc(f["title"]), S_FIND), Paragraph(_esc(f["text"]), S_FIND_TEXT)]])
    t = Table(rows, colWidths=[24 * mm, None])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.9, INK), ("LINEBELOW", (0, 0), (-1, 0), 0.9, INK), ("SPAN", (0, 0), (-1, 0)),
        ("LINEBELOW", (0, 1), (-1, -2), 0.5, RULE_SOFT), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _tech(details):
    t = Table([[Paragraph(_esc(k), S_TECH_K), Paragraph(_esc(v), S_TECH_V)] for k, v in details],
              colWidths=[30 * mm, None])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                           ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE_SOFT)]))
    return t


class _SheetStart(Flowable):
    """Zero-size marker: records which sheet a page belongs to, for the continuation header."""

    def __init__(self, label):
        super().__init__()
        self.label = label

    def wrap(self, *_):
        return 0, 0

    def draw(self):
        doc = self.canv._doctemplate
        doc.sheet_label, doc.sheet_page = self.label, self.canv.getPageNumber()


def _sheet(x, r, created, no):
    when = datetime.fromisoformat(r["scanned_at"]).astimezone(WIB).strftime("%d-%m-%Y %H:%M WIB")
    host = r.get("host") or r["target"]
    out = [_SheetStart(f"{BRAND} · No. {no} · {host} ({x['cont']})"), _letterhead(x, created, no), _title(x),
           _patient(x, r, when)]
    if "error" in r:
        return out + [Spacer(1, 10), Paragraph(_esc(x["failed"].format(error=r["error"])), S_ERR)]
    out += [Spacer(1, 10), Paragraph(x["results"], S_CAP), Spacer(1, 3), _results(x, r), Spacer(1, 4),
            Paragraph(x["legend"], S_LEGEND)]
    if r["findings"]:
        out += [Spacer(1, 12), _conclusion(x, r["findings"])]
    out += [Spacer(1, 12), KeepTogether([Paragraph(x["tech"], S_CAP), Spacer(1, 3), _tech(r["details"])])]
    out += [Spacer(1, 14), Paragraph(f"<b>{x['refs_label']}</b>: {x['refs']}", S_LEGEND)]
    if SITE:
        out.append(Paragraph(_esc(x["method"].format(site=SITE)), S_LEGEND))
    return out


def _batch(x, scan, created, code):
    rows = [[Paragraph(h, S_LABEL) for h in x["batch_head"]]]
    for i, r in enumerate(scan["results"], 1):
        ok = "error" not in r
        rows.append([Paragraph(_esc(r.get("host") or r["target"]), S_CELL_MONO),
                     Paragraph(str(r["score"]) if ok else "–", S_CELL_MONO),
                     Paragraph(r["grade"] if ok else x["batch_fail"], S_CELL_MONO), Paragraph(f"{code}-{i}", S_CELL_MONO)])
    t = Table(rows, colWidths=[None, 20 * mm, 20 * mm, 32 * mm])
    t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("LINEBELOW", (0, 0), (-1, 0), 0.9, INK),
                           ("LINEBELOW", (0, 1), (-1, -1), 0.5, RULE_SOFT), ("TOPPADDING", (0, 0), (-1, -1), 5),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return [_letterhead(x, created, code), Spacer(1, 10), Paragraph(x["batch_title"], S_TITLE), Spacer(1, 2),
            Paragraph(x["batch_sub"].format(n=len(scan["results"]), avg=scan["summary"]["avg"]), S_SUB), Spacer(1, 8), t,
            PageBreak()]


def build_pdf(scan):
    x = TX.get(scan.get("lang"), TX["id"])
    buf = io.BytesIO()
    created = datetime.fromisoformat(scan["created"]).astimezone(WIB)
    code = scan["id"][:8].upper()

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Sans", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(16 * mm, 11 * mm, x["footer"].format(by=MADE_BY))
        canvas.drawRightString(A4[0] - 16 * mm, 11 * mm, x["page"].format(n=doc.page))
        canvas.restoreState()

    def continuation(canvas, doc):
        if getattr(doc, "sheet_page", None) in (None, canvas.getPageNumber()):
            return
        canvas.saveState()
        canvas.setFont("Mono", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(16 * mm, A4[1] - 11 * mm, doc.sheet_label)
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.6)
        canvas.line(16 * mm, A4[1] - 13 * mm, A4[0] - 16 * mm, A4[1] - 13 * mm)
        canvas.restoreState()

    doc = BaseDocTemplate(buf, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=16 * mm,
                          bottomMargin=18 * mm, title=x["doc_title"], author=BRAND)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")
    doc.addPageTemplates([PageTemplate(id="sheet", frames=[frame], onPage=footer, onPageEnd=continuation)])
    story = _batch(x, scan, created, code) if len(scan["results"]) > 1 else []
    for i, r in enumerate(scan["results"], 1):
        if i > 1:
            story.append(PageBreak())
        story += _sheet(x, r, created, f"{code}-{i}")
    doc.build(story)
    return buf.getvalue()
