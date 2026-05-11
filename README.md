<!-- TODO: add banner image before launch (docs/screenshots/banner.png, 1280x640) -->

<div align="center">

<img src="adsreport/ui/assets/logo.svg" height="48" alt="AdsReport logo" />

# AdsReport

**See your Facebook Ads data — on your server, for free, forever.**

[![CI](https://github.com/adsreport/adsreport/actions/workflows/ci.yml/badge.svg)](https://github.com/adsreport/adsreport/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/adsreport?color=4F8DFD)](https://pypi.org/project/adsreport/)
[![License: MIT](https://img.shields.io/badge/license-MIT-22C55E)](LICENSE)
[![Docker Pulls](https://img.shields.io/docker/pulls/ghcr.io/adsreport/adsreport)](https://github.com/adsreport/adsreport/pkgs/container/adsreport)
[![Languages](https://img.shields.io/badge/i18n-pt--BR%20%7C%20en--US-4F8DFD)](#)

<!-- TODO: add gif before publishing — record: docker run → wizard → dashboard with real data (docs/screenshots/dashboard.gif) -->
<!-- ![AdsReport dashboard](docs/screenshots/dashboard.gif) -->

</div>

---

## The problem

The Ads Manager is functional but painful to share with clients. SaaS reporting tools start at US$ 50–500/month, require sending your data to a third party, and lock you into their format.

Spreadsheets are free but you're exporting CSVs every Monday morning like it's 2012.

AdsReport is the alternative: a self-hosted dashboard that reads directly from the Facebook Marketing API, stores everything locally in SQLite, and requires exactly one command to start.

---

## How it compares

|                           | **AdsReport** | SaaS reporting tools | Spreadsheet |
| ------------------------- | :-----------: | :------------------: | :---------: |
| **Cost**                  |     Free      |     $50–500/mo       |    Free     |
| **Your data stays local** |      ✅       |          ❌          |     ✅      |
| **Self-hosted**           |      ✅       |          ❌          |     ❌      |
| **pt-BR**                 |   ✅ Native   |       Rarely         |   Manual    |
| **No App Review needed**  |      ✅       |         N/A          |     N/A     |
| **Open source**           |      ✅       |          ❌          |     ❌      |
| **Setup time**            |    ~5 min     |       30–60 min      | Hours/week  |

---

## What's in v0.1.0

- 📊 &nbsp;9 KPI cards with period-over-period deltas and sparklines
- 📈 &nbsp;Time series chart and spend breakdown by campaign
- 🗂 &nbsp;Campaigns table with native sort and filter
- 🧙 &nbsp;5-step visual wizard — no config files, no terminal after setup
- 🔐 &nbsp;Zero `.env` files — all settings stored in the database
- 🌐 &nbsp;pt-BR and en-US, switchable from the UI
- 🐳 &nbsp;Docker image for `linux/amd64` and `linux/arm64` (Raspberry Pi, Oracle Free Tier)
- 🔄 &nbsp;Background sync on a configurable schedule
- 🔑 &nbsp;Access token encrypted at rest with your admin password

---

## Quickstart

### Docker (recommended)

```bash
docker run -d \
  --name adsreport \
  -p 8050:8050 \
  -v adsreport-data:/data \
  ghcr.io/adsreport/adsreport:latest
```

Open **[http://localhost:8050](http://localhost:8050)** — the setup wizard starts automatically.

### pipx

```bash
pipx install adsreport
adsreport start
```

### docker-compose

```bash
curl -O https://raw.githubusercontent.com/adsreport/adsreport/main/docker-compose.yml
docker compose up -d
```

> 💡 **You'll need a Facebook Developer app in development mode** — no App Review, no cost, takes ~5 minutes. [Step-by-step guide →](docs/facebook-setup.md)

---

## How it works

```
                        ┌─────────────────────────┐
  Your browser  ──────▶ │   Dash UI  (port 8050)  │
                        └────────────┬────────────┘
                                     │
                        ┌────────────▼────────────┐
                        │      Service Layer       │
                        │  Auth · Reports · Sync   │
                        └──────────┬──────────────┘
                                   │
               ┌───────────────────┴──────────────────┐
               │                                       │
   ┌───────────▼───────────┐             ┌────────────▼──────────┐
   │  SQLite (local)        │             │  Facebook Marketing   │
   │  ~/.adsreport/data.db  │             │  API  (read-only,     │
   │  or Docker volume      │             │  dev mode, no cost)   │
   └────────────────────────┘             └───────────────────────┘
```

The app runs as a single Python process. On first boot, it creates the SQLite database and redirects you to the setup wizard. After that, an APScheduler job syncs your ad data in the background on a configurable interval. The UI reads from SQLite — it never calls Facebook's API during page loads.

---

## Available metrics

| Metric          | What it measures                                     |
| --------------- | ---------------------------------------------------- |
| **Impressions** | Number of times your ads appeared on screen          |
| **Clicks**      | Number of times users clicked on your ads            |
| **CTR**         | Clicks ÷ Impressions — how engaging your creative is |
| **CPC**         | Average cost per click                               |
| **CPM**         | Cost per 1,000 impressions                           |
| **Spend**       | Total amount invested in the selected period         |
| **Leads**       | Lead-generation conversion events from your ads      |
| **Conversions** | Custom pixel conversion events                       |
| **ROAS**        | Revenue ÷ Spend — return on ad spend                 |

All metrics support daily, weekly, and monthly breakdowns. Period-over-period comparison is built in.

---

## Roadmap

- [x] **v0.1.0** — Dashboard, 9 KPIs, sync engine, 5-step onboarding wizard, pt-BR + en-US
- [ ] **v0.2.0** — PDF and PNG export of the dashboard
- [ ] **v0.3.0** — Read-only share links (token-based) for clients
- [ ] **v0.4.0** — Google Ads connector (same architecture, new plugin)
- [ ] **v0.5.0** — Multi-user with admin/viewer roles
- [ ] **v1.0.0** — Plugin system for additional connectors (TikTok, LinkedIn)

Have a feature request? [Open an issue.](https://github.com/adsreport/adsreport/issues/new?template=feature_request.yml)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide. Short version:

```bash
git clone https://github.com/adsreport/adsreport
cd adsreport
poetry install
poetry run adsreport start   # dev server on :8050
poetry run pytest tests/unit # test suite
```

Full setup instructions (including Windows-specific steps) at [docs/installation/source.md](docs/installation/source.md).

Browse [`good-first-issue`](https://github.com/adsreport/adsreport/labels/good-first-issue) for approachable tasks. Adding a new language is particularly welcome — see [docs/i18n-contributing.md](docs/i18n-contributing.md), it takes about 30 minutes.

---

## Stack

| Layer            | Technology                                                                                             |
| ---------------- | ------------------------------------------------------------------------------------------------------ |
| UI               | [Dash 2.x](https://dash.plotly.com/) + [Plotly](https://plotly.com/python/)                            |
| Auth             | [Flask-Login](https://flask-login.readthedocs.io/) + [Werkzeug](https://werkzeug.palletsprojects.com/) |
| ORM / Migrations | [SQLAlchemy 2.x](https://docs.sqlalchemy.org/) + [Alembic](https://alembic.sqlalchemy.org/)            |
| Database         | [SQLite](https://www.sqlite.org/) (default) — swappable to Postgres via one URL change                 |
| Facebook API     | [facebook-business SDK](https://github.com/facebook/facebook-python-business-sdk)                      |
| Background jobs  | [APScheduler](https://apscheduler.readthedocs.io/)                                                     |
| Encryption       | [cryptography.fernet](https://cryptography.io/en/latest/fernet/)                                       |
| Logging          | [structlog](https://www.structlog.org/)                                                                |
| Packaging        | [hatch](https://hatch.pypa.io/)                                                                        |

---

## Security

Facebook credentials are encrypted at rest using Fernet (AES-128-CBC + HMAC-SHA256). The key is derived from your admin password via PBKDF2-HMAC-SHA256 with 300,000 iterations. If you lose your password, the secrets are irrecoverable — this is the intended behavior.

See [SECURITY.md](SECURITY.md) for the full threat model and how to report vulnerabilities.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Disclaimer

AdsReport is an independent open source project and is **not affiliated with, endorsed by, or in any way associated with Meta Platforms, Inc.**

"Facebook" and "Meta" are trademarks of Meta Platforms, Inc. The Facebook Marketing API is used solely to read advertising data on behalf of the user who provides their own credentials. AdsReport does not store, transmit, or process user data on any external server.
