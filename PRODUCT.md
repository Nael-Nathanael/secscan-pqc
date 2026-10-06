# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

The Indonesian public who want to understand post-quantum cryptography: developers, IT staff, students, and curious
readers. They arrive from a link, a talk, or a search, read in Bahasa Indonesia, and often on a phone. Most of them cannot
scan anything themselves; the scanner is password-gated.

## Product Purpose

Public education first. SecScan explains what quantum computers threaten in today's cryptography and what to do about it,
and proves it with a real outside-in scanner that grades a server's PQC readiness. Success is a visitor who understands
the threat (harvest now, decrypt later), knows that key exchange can be fixed today while certificates cannot yet, and
shares the page.

## Positioning

Open source (Apache-2.0) with a public, exact scoring method: every weight and rule is on the page and in the code. The
probes are hand-built protocol hellos, read-only. The explanations are sourced and corrected against primary documents
(NIST, IETF, BSSN), in plain Bahasa Indonesia, and avoid fear-selling.

## Operating Context

- Scanner: up to 4 targets per scan, results in seconds, PDF report. Gated by a shared password; visitors without one
  can request access.
- Content source: Nathan's PQC research in `~/pqc` (`catatan-pqc.md`, `facts.md`, `sources.md`, research notes), as of
  October 2026, every claim sourced.
- Hosted at sec-scan.miraestudio.id behind Cloudflare; FastAPI serving static HTML. No build step today.

## Capabilities and Constraints

- Checks: PQ key exchange in TLS 1.3 (weight 100), certificate (60), SSH (50), TLS versions (40). Grades A–E.
- The best score a public site can reach today is 92: no public CA issues ML-DSA certificates yet.
- Scope is the scanner plus educational content from the PQC research. No asset dashboard, registry, user accounts,
  algorithm directory, or crypto tools.
- UI and reports in Bahasa Indonesia.

## Brand Commitments

- Name: **SecScan PQC**, credited "by MiraeStudio.id" with a link to the studio. Its own identity, not the studio's.
- Voice from the research: "santai tapi rapi", accurate, not fear-selling; hype always paired with a counterpoint.
- Must not read as a clone of tahankuantum.com (CISSReC), which uses the same check weights.

## Evidence on Hand

- Real scan results (e.g. miraestudio.id: 92 / A) and PDF reports.
- The `/metodologi` page and the `~/pqc` research: Q-Day estimates, NIST standards, deadlines (US, EU, BSSN), myths,
  Indonesian readiness map (measured 5 Oct 2026).
- No testimonials, user counts, or press. Do not invent them.

## Product Principles

1. Explain before alarming: every threat comes with what is and isn't broken.
2. Show the method: a score is only as credible as its published rules.
3. Read-only, always.
4. Sourced or omitted.
