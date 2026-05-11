# Security Policy

## Threat model

AdsReport is designed to run on your own server, behind a reverse proxy (Caddy, nginx, Traefik) with TLS. The threat model assumes:

- **Trusted local network or HTTPS-only exposure.** Running on plain HTTP over the public internet is unsupported.
- **Single-user or small-team deployment.** Not a multi-tenant SaaS.
- **Physical access to the server is out of scope.** If an attacker has your disk, the encrypted secrets are at risk.

## What is protected

- **Facebook access tokens** are always encrypted at rest using Fernet (AES-128-CBC + HMAC-SHA256). The key is derived from your admin password via PBKDF2-HMAC-SHA256 (300 000 iterations). If you forget your password, the tokens are irrecoverable — this is intentional.
- **Session cookies** are HTTP-only, SameSite=Lax.
- **Login endpoint** is rate-limited: 5 attempts per 15 minutes per IP.

## What is NOT protected

- An attacker with read access to `~/.adsreport/data.db` AND `~/.adsreport/.salt` AND your admin password can decrypt all secrets.
- The app has no protection against a compromised host OS.

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Email **security@adsreport.dev** with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Your name/handle (for credit in the advisory)

We target a response within 48 hours and a fix within 90 days of the report. We will coordinate disclosure with you before publishing.
