# Security policy

## Reporting a vulnerability

Please report vulnerabilities privately through
[GitHub private vulnerability reporting](https://github.com/Nael-Nathanael/secscan-pqc/security/advisories/new),
not as a public issue. Expect an acknowledgement within 7 days.

Relevant reports include:

- Ways to make the scanner reach private or internal addresses (SSRF), for example via DNS rebinding or redirects
- Ways to make it send more than protocol hellos to a target
- Bypasses of the password, rate limit or target limits
- Injection into the web UI or the PDF report

Wrong scores and probes that misread a server are bugs, not vulnerabilities. Please open a normal issue for those.

## Supported versions

Only the latest commit on `main` gets fixes.
