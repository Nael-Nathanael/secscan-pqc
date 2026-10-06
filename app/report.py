"""PDF report in the same shape as the sample scan reports."""

import io
import math
import os
from datetime import datetime

from reportlab.graphics.shapes import Circle, Drawing, Line, Polygon
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Flowable, HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from scanner import WIB

BRAND = os.environ.get("BRAND_NAME", "SecScan PQC")
SITE = os.environ.get("SITE_NAME", "")
MADE_BY = f"{BRAND}, {SITE}" if SITE else BRAND

INK = colors.HexColor("#111827")
MUTED = colors.HexColor("#6b7280")
LINE = colors.HexColor("#d1d5db")
BLUE = colors.HexColor("#2563eb")
GREEN = colors.HexColor("#15803d")
LIME = colors.HexColor("#65a30d")
ORANGE = colors.HexColor("#d97706")
DORANGE = colors.HexColor("#ea580c")
RED = colors.HexColor("#dc2626")
GRADE_COLORS = {"A": GREEN, "B": LIME, "C": ORANGE, "D": DORANGE, "E": RED}
LEVEL = {
    "crit": (RED, colors.HexColor("#fef2f2")),
    "high": (colors.HexColor("#b45309"), colors.HexColor("#fffbeb")),
    "info": (colors.HexColor("#1d4ed8"), colors.HexColor("#eff6ff")),
    "good": (GREEN, colors.HexColor("#f0fdf4")),
}

REFERENCES = (
    "NIST FIPS 203 (ML-KEM), FIPS 204 (ML-DSA), FIPS 205 (SLH-DSA) dan NIST IR 8547 (transisi ke PQC); "
    "IETF draft-ietf-tls-ecdhe-mlkem (X25519MLKEM768); catatan rilis OpenSSL 3.5 dan OpenSSH 9.9/10.0; "
    "serta publikasi Badan Siber dan Sandi Negara (bssn.go.id) terkait migrasi kriptografi tahan kuantum."
)


def _s(name, **kw):
    base = dict(fontName="Helvetica", fontSize=9, leading=12, textColor=INK)
    base.update(kw)
    return ParagraphStyle(name, **base)


S_TITLE = _s("t", fontName="Helvetica-Bold", fontSize=17, leading=21)
S_SUB = _s("sub", fontSize=8.5, textColor=MUTED)
S_H2 = _s("h2", fontName="Helvetica-Bold", fontSize=13, leading=17, spaceBefore=8, spaceAfter=4)
S_HOST = _s("host", fontName="Helvetica-Bold", fontSize=14, leading=17)
S_SCORE = _s("score", fontName="Helvetica-Bold", fontSize=22, leading=24, alignment=TA_RIGHT)
S_SMALL = _s("small", fontSize=7.5, textColor=MUTED)
S_NOTE = _s("note", fontName="Helvetica-Oblique", fontSize=7.5, textColor=colors.HexColor("#9ca3af"))
S_CELL = _s("cell", fontSize=8.5, leading=11)
S_CELLB = _s("cellb", fontName="Helvetica-Bold", fontSize=8.5, leading=11)
S_REF = _s("ref", fontSize=8, leading=11, textColor=MUTED)


def _esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def logo(size=34):
    d = Drawing(size, size)
    c = size / 2
    d.add(Circle(c, c, c - 1, fillColor=BLUE, strokeColor=None))
    r = size * 0.28
    pts = []
    for i in range(6):
        a = math.pi / 6 + i * math.pi / 3
        pts += [c + r * math.cos(a), c + r * math.sin(a)]
    d.add(Polygon(pts, fillColor=None, strokeColor=colors.white, strokeWidth=1.6))
    d.add(Circle(c, c, size * 0.07, fillColor=colors.white, strokeColor=None))
    d.add(Line(c, c, c + r * 1.25, c - r * 1.25, strokeColor=colors.white, strokeWidth=1.6))
    return d


class Badge(Flowable):
    def __init__(self, text, color, w=20, h=13, size=8):
        super().__init__()
        self.text, self.color, self.width, self.height, self.size = text, color, w, h, size

    def draw(self):
        c = self.canv
        c.setFillColor(self.color)
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.4)
        c.roundRect(0, 0, self.width, self.height, 2.5, fill=1, stroke=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", self.size)
        c.drawCentredString(self.width / 2, (self.height - self.size) / 2 + 1.5, self.text)


class Bar(Flowable):
    def __init__(self, pct, w=114 * mm, h=4.2 * mm):
        super().__init__()
        self.pct, self.width, self.height = pct, w, h

    def draw(self):
        c = self.canv
        p = self.pct
        col = GREEN if p >= 90 else BLUE if p >= 50 else ORANGE if p > 0 else None
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.6)
        c.setFillColor(colors.HexColor("#f3f4f6"))
        c.roundRect(0, 0, self.width, self.height, self.height / 2, fill=1, stroke=1)
        if col and p > 0:
            c.setFillColor(col)
            c.roundRect(0, 0, max(self.height, self.width * p / 100), self.height, self.height / 2, fill=1, stroke=1)


def _header(created):
    title = Paragraph(f"Laporan Hasil Scan Kesiapan PQC<br/>PQC Readiness oleh {_esc(BRAND)}", S_TITLE)
    site = f"{_esc(SITE)} | " if SITE else ""
    sub = Paragraph(f"{site}dibuat {created.strftime('%d-%m-%Y %H:%M:%S')} WIB | "
                    f"scan read-only dari sisi luar", S_SUB)
    t = Table([[logo(), [title, Spacer(1, 3), sub]]], colWidths=[16 * mm, None])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 1.2, BLUE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
    ]))
    return t


def _summary(summary):
    head = [Paragraph("Rata-rata skor (nilai 1-100)", S_SMALL)]
    vals = [Paragraph(f"<font color='#2563eb'><b>{summary['avg']}</b></font>", _s("avg", fontSize=18, leading=20))]
    for g in "ABCDE":
        head.append(Paragraph(f"Grade {g}", S_SMALL))
        vals.append(Badge(str(summary["grades"][g]), GRADE_COLORS[g]))
    head.append(Paragraph(f"Host dipindai: {summary['hosts']}", S_SMALL))
    vals.append("")
    t = Table([head, vals], colWidths=[48 * mm] + [20 * mm] * 5 + [None])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f9fafb")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def _host_block(r):
    out = [Paragraph(f"Hasil scan: {_esc(r.get('host') or r['target'])}", S_H2)]
    when = datetime.fromisoformat(r["scanned_at"]).strftime("%Y-%m-%d %H:%M:%S")
    if "error" in r:
        out.append(Paragraph(f"{_esc(r['target'])} — <font color='#dc2626'>gagal: {_esc(r['error'])}</font>", S_CELL))
        return out
    port = f":{r['port']}" if r["port"] != 443 else ""
    top = Table([
        [Paragraph(_esc(r["host"] + port), S_HOST), Paragraph(str(r["score"]), S_SCORE)],
        [Paragraph(f"scan {when} &nbsp;|&nbsp; durasi {r['duration']} dtk &nbsp;|&nbsp; IP {r['ip']} "
                   f"&nbsp;|&nbsp; status PQC: <b>{r['pqc_status']}</b>", S_SMALL),
         Badge(r["grade"], GRADE_COLORS[r["grade"]], w=24, h=13)],
    ], colWidths=[None, 26 * mm])
    top.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING", (0, 0), (0, -1), 0), ("RIGHTPADDING", (1, 0), (1, -1), 0),
    ]))
    out.append(top)
    out.append(Spacer(1, 4))

    rows = [[Paragraph(f"{c['label']} (max {c['max']})", S_CELL), Bar(c["pct"]),
             Paragraph(f"<b>{c['pct']}%</b>", _s("p", fontSize=8, alignment=TA_RIGHT))]
            for c in r["components"]]
    bars = Table(rows, colWidths=[40 * mm, 118 * mm, None])
    bars.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (0, -1), 0),
                              ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)]))
    out.append(bars)
    weights = ", ".join(f"{c['label']} {c['max']}" for c in r["components"])
    out.append(Spacer(1, 4))
    out.append(Paragraph(f"Skor komposit {r['score']}/100 dari bobot {weights}", S_NOTE))
    out.append(Spacer(1, 6))

    det = Table([[Paragraph(_esc(k), S_CELLB), Paragraph(_esc(v), S_CELL)] for k, v in r["details"]],
                colWidths=[32 * mm, None])
    det.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e7eb")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    out.append(det)

    if r["findings"]:
        out.append(Paragraph("Temuan dan rekomendasi", S_H2))
        frows, styles = [], [("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOX", (0, 0), (-1, -1), 0.4, LINE)]
        for i, f in enumerate(r["findings"]):
            fg, bg = LEVEL[f["level"]]
            frows.append([Paragraph(f"<b>{_esc(f['title'])}</b>", _s(f"f{i}", fontSize=8.5, leading=11, textColor=fg)),
                          Paragraph(_esc(f["text"]), S_CELL)])
            styles.append(("BACKGROUND", (0, i), (-1, i), bg))
        ft = Table(frows, colWidths=[68 * mm, None])
        ft.setStyle(TableStyle(styles))
        out.append(ft)
    return out


def build_pdf(scan):
    buf = io.BytesIO()
    created = datetime.fromisoformat(scan["created"]).astimezone(WIB)

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#9ca3af"))
        canvas.drawCentredString(A4[0] / 2, 12 * mm, f"Dibuat oleh {MADE_BY} | halaman {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm,
                            topMargin=14 * mm, bottomMargin=20 * mm,
                            title="Laporan Scan PQC Readiness", author=BRAND)
    story = [_header(created), Spacer(1, 8), _summary(scan["summary"]), Spacer(1, 6)]
    for r in scan["results"]:
        blk = _host_block(r)
        story.append(KeepTogether(blk[:4]))
        story += blk[4:]
        story.append(Spacer(1, 8))
    story.append(KeepTogether([
        HRFlowable(width="100%", thickness=0.6, color=LINE, spaceAfter=4),
        Paragraph("<b>Sumber rujukan</b>", S_CELL),
        Paragraph(REFERENCES, S_REF),
        *([Paragraph(f"Cara menghitung skor: https://{_esc(SITE)}/metodologi", S_REF)] if SITE else []),
    ]))
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
