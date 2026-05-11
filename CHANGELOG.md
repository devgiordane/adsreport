# Changelog

All notable changes to AdsReport are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project scaffold
- SQLAlchemy models for all entities (users, settings, ad_accounts, campaigns, adsets, ads, insights, sync_runs, audit_log)
- Alembic migration setup
- Core utilities: crypto (Fernet + PBKDF2), structured logging, Result type, error hierarchy
- i18n system with pt-BR and en-US locales
- Facebook Marketing API client wrapper
- APScheduler-based sync scheduler
- 5-step onboarding wizard
- Dashboard with 9 KPI cards, time series chart, breakdown chart, top campaigns table
- Campaigns page with sortable/filterable table
- Settings page (General, Facebook, Sync, Appearance, Language, About tabs)
- Docker image (linux/amd64 + linux/arm64)
- CI pipeline (lint + typecheck + tests)

## [0.1.0] - TBD

First public release.
