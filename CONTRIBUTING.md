# Contributing to AdsReport

Thanks for your interest! AdsReport is a community project and contributions of all kinds are welcome.

## Quick start for contributors

```bash
git clone https://github.com/adsreport/adsreport
cd adsreport
poetry install --all-extras       # installs dev tools (pytest, ruff, mypy)
poetry run adsreport start        # dev server on :8050
poetry run pytest tests/unit/     # test suite
poetry run ruff check adsreport   # lint
poetry run mypy adsreport         # type-check
```

Full setup guide (including the Windows system Python issue) at [docs/installation/source.md](docs/installation/source.md).

## What we need help with

Good first issues (labeled [`good-first-issue`](https://github.com/adsreport/adsreport/labels/good-first-issue)):

- **Translate to a new language** — create `adsreport/i18n/locales/xx-YY.json` from the `en-US.json` template. See [i18n-contributing.md](docs/i18n-contributing.md).
- **Add a KPI card** — impressions, video views, engagement rate, etc.
- **Improve empty states** — better illustrations for "no data" screens.
- **Write integration tests** — we use VCR.py to record/replay Facebook API responses.
- **ARM Docker testing** — validate the image on Raspberry Pi / Oracle Free Tier.

## Rules

1. **No `.env` files.** All configuration lives in the `app_settings` table. Never add environment variable reading to the app code (the `--data-dir` CLI flag is the only exception).
2. **No hardcoded UI strings.** Every user-visible string goes through `t("key")`. CI enforces this.
3. **No new dependencies without discussion.** Open an issue first if you need a new package.
4. **Tests for services.** New service code requires unit tests. Aim for 80% coverage on `adsreport/services/`.
5. **Type hints everywhere.** `mypy --strict` must pass. No `Any` without a comment explaining why.
6. **One PR, one concern.** Split unrelated changes into separate PRs.

## Code style

- `ruff` for linting and formatting. Run `poetry run ruff format adsreport` before committing.
- `mypy --strict` for types.
- SQLAlchemy 2.x style (`Mapped[...]`, `mapped_column`). No legacy `Column(...)`.
- Service layer only — no Facebook SDK calls from UI callbacks. UI → Service → Repository → DB.

## Adding a new locale

See [docs/i18n-contributing.md](docs/i18n-contributing.md) for the full guide. Short version:

1. Copy `adsreport/i18n/locales/en-US.json` to `xx-YY.json`.
2. Translate every value (keep the keys identical).
3. Add the locale to `SupportedLocale` enum in `constants.py`.
4. The CI key-parity check will catch missing or extra keys.

## Pull request checklist

- [ ] `poetry run pytest` passes
- [ ] `poetry run ruff check adsreport` passes
- [ ] `poetry run mypy adsreport` passes
- [ ] New public functions have type hints
- [ ] New UI strings use `t("key")` and exist in both `en-US.json` and `pt-BR.json`
- [ ] PR description explains *why*, not just *what*

## Questions?

Open a [Discussion](https://github.com/adsreport/adsreport/discussions) or file a [question issue](https://github.com/adsreport/adsreport/issues/new?template=question.yml).
