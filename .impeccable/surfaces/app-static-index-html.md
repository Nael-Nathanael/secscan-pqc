---
version: 1
slug: "app-static-index-html"
primary_target: "app/static/index.html"
related_targets: ["app/static/metodologi.html","app/report.py"]
---

## Scope

Persuade (home: sheet + request slip + leaflet), Read (/metodologi), plus the PDF report. Bahasa Indonesia, 360px up. Scanner logic, scores and API unchanged. Password kept; "Minta kode akses" goes to wa.me/6289503386642 with a prefilled message.

## Audience and job

Indonesian public learning PQC, often on phones. Most cannot scan. Leave knowing: key exchange is fixable today, certificates are not yet; how to read a score. Proof is real only: the miraestudio.id 92 / A sample (labelled contoh), the method, the ~/pqc research. No invented credentials, doctors, signatures, accreditation.

## Direction contract

THESIS: A server's PQC readiness reads like a clinic lab result: each check against its reference value, flags where out of range, a conclusion, and the leaflet that teaches you to read it. Refuses the scanner landing page (hero, scan box, stat strip, rounded explainer cards).

OWN-WORLD: Clinical white sheet, near-black ink, hairline ruled result tables, teal for in-range, red only for flags, a pale teal tint for the request slip. Atkinson Hyperlegible Next for text, Atkinson Hyperlegible Mono for values, codes and numbers. Flag letters (H/L/!) in boxed cells. No rounded cards, no shadows beyond paper lift, no gradients.

STORY: See a real result sheet, understand what each row means from its reference column, read the leaflet (threat, standards, why certs lag, deadlines, myths, fixes), request a code or scan.

FIRST VIEWPORT: Left/main: the result sheet at near full width on desktop (header with patient = host, IP, time, no. pemeriksaan; results table Pemeriksaan · Hasil · Nilai rujukan · Flag · Bobot; total + grade; Kesimpulan). Right: the request slip (targets, test panels, kode akses, Periksa button, "Minta kode akses"). Mobile: slip first, then sheet.

FORM: Hasil Laboratorium, IMPECCABLE'S PICK (my #1 of 7), seed ca3e85fd.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Signature

On scan return the sheet prints row by row (clip reveal, ~60ms stagger), flags stamp last. Reduced motion: final sheet at once.
