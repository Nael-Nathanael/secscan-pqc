---
name: SecScan PQC
description: A server's post-quantum readiness, printed as a clinic lab result sheet.
colors:
  desk: "#eef1f0"
  paper: "#ffffff"
  ink: "#1d2321"
  muted: "#56615d"
  rule: "#c9d1ce"
  rule-soft: "#e3e8e6"
  teal: "#00705f"
  teal-tint: "#e4f1ee"
  red: "#c0262b"
  slip-edge: "#b7d6cf"
  slip-rule: "#c6ddd7"
  field-stroke: "#9fbfb8"
typography:
  headline:
    fontFamily: "Atkinson Next, system-ui, sans-serif"
    fontSize: "clamp(26px, 3.4vw, 38px)"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.015em"
  page-title:
    fontFamily: "Atkinson Next, system-ui, sans-serif"
    fontSize: "clamp(24px, 2.6vw, 32px)"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.015em"
  title:
    fontFamily: "Atkinson Next, system-ui, sans-serif"
    fontSize: "22px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  sheet-title:
    fontFamily: "Atkinson Next, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "0.06em"
  body:
    fontFamily: "Atkinson Next, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.55
    fontFeature: "\"tnum\""
  label:
    fontFamily: "Atkinson Next, system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.4
  value:
    fontFamily: "Atkinson Mono, ui-monospace, monospace"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.35
  score:
    fontFamily: "Atkinson Mono, ui-monospace, monospace"
    fontSize: "34px"
    fontWeight: 700
    lineHeight: 1
  flag:
    fontFamily: "Atkinson Mono, ui-monospace, monospace"
    fontSize: "14px"
    fontWeight: 700
    lineHeight: 1
  level:
    fontFamily: "Atkinson Mono, ui-monospace, monospace"
    fontSize: "11px"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "0.08em"
rounded:
  none: "0px"
spacing:
  gap: "clamp(16px, 2.4vw, 28px)"
  sheet: "clamp(18px, 3vw, 32px)"
  slip: "20px"
  cell: "10px"
  wrap: "1180px"
  slip-width: "340px"
components:
  sheet:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "{spacing.sheet}"
  request-slip:
    backgroundColor: "{colors.teal-tint}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "{spacing.slip}"
    width: "{spacing.slip-width}"
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "14px"
    width: "100%"
  button-primary-hover:
    backgroundColor: "#000000"
  button-primary-disabled:
    backgroundColor: "{colors.muted}"
  input-field:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.value}"
    rounded: "{rounded.none}"
    padding: "9px 10px"
  flag-low:
    textColor: "{colors.red}"
    typography: "{typography.flag}"
    rounded: "{rounded.none}"
    padding: "4px 4px 3px"
  flag-critical:
    backgroundColor: "{colors.red}"
    textColor: "{colors.paper}"
    typography: "{typography.flag}"
    rounded: "{rounded.none}"
    padding: "4px 4px 3px"
  grade-box:
    textColor: "{colors.ink}"
    typography: "{typography.flag}"
    rounded: "{rounded.none}"
    padding: "5px 7px 4px"
  sample-tag:
    textColor: "{colors.muted}"
    rounded: "{rounded.none}"
    padding: "4px 6px 3px"
---

# Design System: SecScan PQC

## Overview

**Creative North Star: "Hasil Laboratorium"**

Every surface is a clinic lab result sheet lying on a pale desk. A server is the patient; each check is a row read against its reference value; out-of-range rows carry a boxed flag; a composite score and grade close the table; a Kesimpulan box gives the doctor's reading; a leaflet teaches the reader how to interpret it. The look is borrowed from real Indonesian lab printouts: white paper, near-black ink, hairline rules, a ruled table that does the talking. Nothing is decorated that a lab printer would not print.

Density is tabular and calm. Text is set in Atkinson Hyperlegible Next, chosen for legibility on phones; every measured value, code, number and identifier is set in Atkinson Hyperlegible Mono with tabular figures, so results line up like a printout. Colour is clinical and scarce: teal says "in range" and "this is a link", red says "out of range", and nothing else gets a hue. The PDF report is the same sheet, not a separate design.

The world refuses the scanner landing page: no hero band, no centred scan box, no stat strip, no rounded explainer cards, no gradient atmosphere.

**Key Characteristics:**
- Paper sheets on a desk, square corners, lift only from the paper's own shadow.
- Results as a ruled table: Pemeriksaan, Hasil, Nilai rujukan, Nilai, Flag, Bobot.
- Mono for every value; sans for every word.
- Red appears only where a result falls below its reference.
- The request slip is a pale teal form tucked beside the sheet, perforated along its top.
- Rows print in one by one, flags stamp last.

**Open, not part of the system yet:** three ideas were raised and deferred. Do not build them as if they were established: the leaflet as a physical paper object (folded leaflet rather than a white band), the reference range drawn as a scale on each row, and a display voice derived from the sheet header for larger headings.

## Colors

A near-monochrome clinical palette, warm-neutral greys with a green cast, plus one teal and one red that carry meaning, never mood.

### Primary
- **Lab Teal** (`teal`): the in-range colour. In-range result values, the in-range flag cell, the BAIK level, every link (underlined, 1px, 3px offset; 2px on hover), the focus ring, caret, checkbox accent and the "Rincian teknis" disclosure.
- **Slip Tint** (`teal-tint`): background of the request slip and text selection. Its own rules: Slip Edge (`slip-edge`) for the slip border, Slip Rule (`slip-rule`) between test panels and above the access request, Field Stroke (`field-stroke`) on inputs inside the slip; the perforation is a 2px dashed line in a deeper teal-grey (#8fbfb4).

### Secondary
- **Flag Red** (`red`): out-of-range only. The L flag (red letter, red 1.5px box), the ! flag (white on solid red), KRITIS and PERHATIAN levels, scan errors and form error status.

### Neutral
- **Desk** (`desk`): the page behind the sheets, the footer, and code blocks in the leaflet.
- **Paper** (`paper`): sheets, letterhead, leaflet band, inputs.
- **Ink** (`ink`): text, the 2px rule under the sheet head and above the total, the 1px rule under column heads, the Kesimpulan box, the grade box, the brand code box, and the Periksa button.
- **Muted Ink** (`muted`): labels, column heads, reference values, sheet number, footnotes, CATATAN level, CONTOH tag, disabled button.
- **Rule** (`rule`): structural hairlines: letterhead and patient-block bottoms, sheet foot, leaflet topic dividers.
- **Soft Rule** (`rule-soft`): row separators inside every table.

### Named Rules
**The Flag Red Rule.** Red marks a result below its reference value, an error, or a finding that needs attention. It is never a brand accent, never a button, never a highlight.

**The Teal Means In-Range Rule.** Teal on a value means the value meets its reference. Elsewhere teal only marks interaction: links (always underlined), focus, caret. A teal headline or a teal panel fill other than the slip is off-system.

**The CONTOH Rule.** The sample sheet is tagged CONTOH in a muted outlined mono tag. It stays muted; a sample is not a warning and gets neither red nor teal.

## Typography

**Body Font:** Atkinson Hyperlegible Next (`Atkinson Next`, variable 200–800, with system-ui)
**Label/Mono Font:** Atkinson Hyperlegible Mono (`Atkinson Mono`, variable 200–800, with ui-monospace)

**Character:** A legibility-first pairing from the same family: the sans reads like a careful clinic form, the mono like the printer's output. Weight does the hierarchy work (400 and 700 only); the scale stays small.

### Hierarchy
- **Headline** (700, clamp 26–38px, 1.2, -0.015em): the leaflet's opening heading, max 24ch.
- **Page title** (700, clamp 24–32px, 1.2, -0.015em): the one h1 above the desk, max 34ch.
- **Title** (700, 22px, 1.2): leaflet topic headings; method-page sheet headings use 20px.
- **Sheet title** (700, 15px, 0.06em, uppercase): the printed heading of a sheet ("Hasil pemeriksaan kesiapan PQC") and the slip ("Formulir pemeriksaan"). Table captions and the Kesimpulan heading use the same treatment at 13px. These are the form's own printed titles, not decoration above a headline.
- **Body** (400, 16px, 1.55): leaflet and method prose at 64–72ch; table cells at 15px; sheet notes at 13–14px.
- **Label** (400, 12px, muted): column heads, patient-block labels, field hints, legend.
- **Value** (mono 400, 15px, 1.35): host, IP, time, results, codes, technical details (13px), weights in the slip (12px).
- **Score** (mono 700, 34px, 1): the composite score, with "/100" at 16px.
- **Flag / Level** (mono 700, 14px / 11px +0.08em): flag letters, grade, conclusion levels (KRITIS, PERHATIAN, CATATAN, BAIK).

### Named Rules
**The Printer Rule.** If it was measured, counted, or is an identifier (score, weight, IP, cipher name, sheet number, numeric table cells), it is mono and right-aligned when numeric. Words about it are sans.

**The Tabular Figures Rule.** The whole page sets `font-variant-numeric: tabular-nums`; numbers never shift column.

## Layout

A centred column (`wrap`, padded by `gap`) holds a letterhead, a short intro, then the **desk**: a two-column grid with the sheets in a flexible main column and the request slip fixed at `slip-width`, top-aligned and sticky 16px from the top. Below the desk the leaflet runs full width on paper; each topic is a 260px label column (heading plus "Baris ..." row references back to the sheet) beside a body of max 70ch, separated by rules, the first topic opened by a 2px ink rule.

The method page is the same world as a document: its sections are sheets **joined edge to edge**, the first with the full paper lift, each following sheet butted against it with a 1px rule and only the lower shadow, so they read as one continuous printout. A boxed key statement (1px ink border, 17px) sits above them; the table of contents is itself a sheet with two columns.

Rhythm comes from table cell padding (10px vertical in results, 6–8px elsewhere, 10px right gutter, no left padding) and from `gap` between blocks.

**Responsive:**
- **Under 960px:** the desk becomes one column and the slip moves above the sheet and stops being sticky.
- **Under 760px:** leaflet topics stack, heading above body.
- **Under 680px:** the results table becomes a stacked grid per row: name and value on the left, flag on the right spanning both, "Rujukan:" prefixed reference beneath, then labelled Nilai and Bobot. Column heads are hidden; labels come from the cells.
- **Under 600px:** the letterhead nav drops to its own single, non-wrapping row (14px, 16px gaps); the method TOC goes to one column.
- **Under 560px:** the patient block goes to two columns; conclusion rows stack level above text; myth rows stack; wide leaflet and method tables keep a 500px minimum and scroll sideways inside a box with soft edge shadows.
- **Under 420px:** the sheet title tightens to 13px, 0.03em.

## Elevation & Depth

Flat paper on a flat desk. The only depth is the lift of a sheet of paper, and it is earned by being a sheet.

### Shadow Vocabulary
- **Paper lift** (`box-shadow: 0 1px 1px rgb(29 35 33 / .1), 0 6px 14px -8px rgb(29 35 33 / .22)`): every result sheet and method sheet.
- **Joined sheet** (`box-shadow: 0 6px 14px -8px rgb(29 35 33 / .22)` plus a 1px `rule` top border): method sheets that continue the one above.
- **Slip of paper** (`box-shadow: 0 1px 1px rgb(29 35 33 / .1)`): the batch summary above multiple sheets.
- **Scroll edge** (radial `rgb(29 35 33 / .18)` fading 10px, masked by `paper` local gradients): wide tables on phones, telling the reader there is more to the side.

### Named Rules
**The Paper Lift Rule.** Only paper casts a shadow. Buttons, fields, flags, the slip and the leaflet are flat. No hover lift, no glow.

**The Functional Gradient Rule.** Gradients exist only as the scroll-edge affordance on overflowing tables. No decorative or atmospheric gradients.

## Shapes

Square everything (`rounded.none`): sheets, slip, inputs, button, flags, grade, tags. Boxes are drawn with strokes the way a printed form draws them: 1.5px for marks that must be read at a glance (brand code PQ, L flag, grade), 1px for containers (Kesimpulan, key statement, CONTOH tag, inputs). Horizontal rules carry structure: 2px ink to open and close a section (sheet head, total, first leaflet topic), 1px ink under column heads, 1px `rule` between blocks, 1px `rule-soft` between rows. The slip's only flourish is a dashed perforation along its top edge.

## Components

### Buttons
Blunt and full-width, like the submit strip at the bottom of a paper form.
- **Shape:** square, no border.
- **Primary (Periksa):** ink fill, white 16px bold sans, 14px padding, full slip width.
- **Hover / Focus:** hover goes to pure black; focus is the global 2px teal outline offset 2px.
- **Disabled:** muted fill with a progress cursor while a scan runs; the status line below counts seconds.
- There are no secondary buttons. Other actions (PDF, "Minta lewat WhatsApp", "Cara membaca") are underlined teal links.

### Inputs / Fields
- **Style:** paper fill, 1px `field-stroke`, square, 15px mono text, 9px 10px padding; the target textarea is 104px tall and resizes vertically. Label above in 13px bold sans; hint below in 12px muted.
- **Focus:** 2px teal outline inset by 1px.
- **Test panels:** checkbox rows on `slip-rule` separators: teal-accented checkbox, panel name, weight in 12px muted mono ("bobot 100") at the right.
- **Error:** the status line under the button turns red; fields themselves do not change colour.

### Navigation
The letterhead: a white band with a 1px `rule` bottom. Brand is a boxed mono "PQ" code, "SecScan PQC" in 18px bold, and "oleh MiraeStudio.id" in 13px muted. Nav links sit right in 15px ink, no underline; hover and the current page turn teal and underlined. Under 600px the nav takes its own row.

### Result Sheet (signature)
The core of the system, identical on screen and in the PDF.
- **Sheet head:** uppercase sheet title, "Diperiksa dari luar, read-only" subline, and at right the mono "No." sheet number with the CONTOH tag on the sample; closed by a 2px ink rule.
- **Patient block:** three label/value cells (Host, Alamat IP, Waktu pemeriksaan in WIB), label 12px muted, value 15px mono, `rule` beneath.
- **Results table:** caption "Hasil"; columns Pemeriksaan · Hasil · Nilai rujukan · Nilai · Flag · Bobot. In-range values are teal mono; out-of-range values are bold ink mono. References are muted.
- **Flags:** in range, an empty cell; 50–99, **L** in a red 1.5px box; below 50, **!** white on solid red. There is no H flag; a result cannot exceed its reference.
- **Total:** a 2px ink rule, then "Skor komposit, status ...", the 34px mono score with /100, and the grade letter in a 1.5px ink box. A muted legend explains L, !, and the weighting, linking to the method.
- **Kesimpulan:** a 1px ink box; each finding is a 92px level column (KRITIS and PERHATIAN red, CATATAN muted, BAIK teal, mono 11px) beside a bold title and muted explanation.
- **Rincian teknis:** a closed disclosure in teal; key column muted at 140px, values in 13px mono.
- **Sheet foot:** `rule` top border, "Akhir hasil · durasi N detik" at left, PDF link (bold) at right.

### Request Slip (signature)
A tear-off request form: `teal-tint` fill, 1px `slip-edge` border, dashed perforation on top, `slip` padding. Uppercase title, a muted lede, the target field, the test panels, the access-code field, the Periksa button, a status line, then "Belum punya kode akses?" with a WhatsApp link above a `slip-rule`, and a 12px muted consent line.

### Leaflet Topic
A reading section in the leaflet: heading and "Baris ..." row links on the left, prose, tables and code blocks on the right. Myths are a two-column list with the myth struck through in bold ink (2px strike) and the correction beside it.

### Motion: print feed and flag stamp
When a scan returns, the sheet is printed: each results row, the total row and the Kesimpulan box reveal top-down (`clip-path` inset plus a 6px drop, 380ms, `cubic-bezier(.16, 1, .3, 1)`, 70ms stagger by row index). Each flag then stamps in (scale 1.5 to 1 with fade, 300ms) 420ms after its row. The sample sheet on load does not animate. Under `prefers-reduced-motion: reduce` none of this runs; the finished sheet appears at once and the scroll to it is instant.

### PDF Report
The same sheet on A4 (16mm margins): letterhead with boxed PQ and the sheet number plus creation time in mono; uppercase title over a 1.6pt ink rule; patient block; results table with the same columns, teal in-range values, bold out-of-range values, and the same L / ! flag boxes; total with score and boxed grade; Kesimpulan box with coloured levels; Rincian teknis (kept on one page); references line. Continuation pages carry a mono "(lanjutan)" header over a `rule` line; every page footer reads who made it and "halaman N". Several hosts get a "Ringkasan pemeriksaan" summary page first.

## Do's and Don'ts

### Do:
- **Do** put every new result, score, or check into the sheet anatomy: row with its reference value, flag, weight, then the total and Kesimpulan.
- **Do** set every measured value, code, and number in Atkinson Hyperlegible Mono with tabular figures; right-align numeric columns.
- **Do** keep red for below-reference results, errors, and attention-level findings only.
- **Do** underline every teal link (1px, 3px offset, 2px on hover).
- **Do** carry any change to the web sheet into `app/report.py` in the same change: same columns, flags, colours, levels and order (Key exchange PQ, Sertifikat, SSH, Versi TLS).
- **Do** tag sample output CONTOH in the muted outlined tag.
- **Do** keep the print-feed reveal behind `prefers-reduced-motion: no-preference`.
- **Do** keep the slip's own teal-grey rules inside the slip; the sheet uses ink, `rule` and `rule-soft`.

### Don't:
- **Don't** round corners on anything.
- **Don't** add shadows to anything that is not a sheet of paper, and don't add hover lift.
- **Don't** use gradients except the scroll-edge affordance on overflowing tables.
- **Don't** use red or teal as decoration or headline colour; the only red fill is the ! flag, and the slip tint is the only coloured surface.
- **Don't** build a hero, a centred scan box, a stat strip, or rounded explainer cards.
- **Don't** invent credentials on the sheet: no doctor, signature, stamp of approval or accreditation mark.
- **Don't** colour the CONTOH tag.
