# Contributing

Issues and pull requests are welcome in English or Bahasa Indonesia.

## Setup

```sh
python -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/ruff check .
.venv/bin/pytest
```

Run the app with `cd app && ../.venv/bin/uvicorn main:app --reload`, then open http://127.0.0.1:8000.

## Guidelines

- Keep it small. The scanner uses the standard library plus `cryptography`; add a dependency only when the standard library
  cannot do the job.
- Changing a score or weight in `app/scanner.py` means updating `app/static/metodologi.html` in the same pull request.
  `tests/test_api.py` fails when the two disagree.
- Every new scoring branch needs a test in `tests/test_scanner.py`. The tests stub the network, so they run offline.
- User-facing text ships in Bahasa Indonesia and English. Scanner, API and finding strings live in `app/i18n.py`, PDF
  labels in `TX` in `app/report.py`, page-script strings in `T` in `app/static/app.js`, and each page has an Indonesian
  and an English file. Change both languages in the same pull request. Code, comments and commit messages are in English.
- Claims on the methodology page need a source, preferably a primary one (NIST, IETF, BSSN, vendor release notes).
- Never send anything beyond protocol hellos to a target. SecScan must stay read-only.

## Pull requests

Describe what changed and how you verified it. For probe changes, name a public host you tested against and the result
you got, plus the matching `openssl s_client` or `ssh -vv` output.
