# Public Portals Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline; whole-change independent review before publication. The user's approved host split and “siga” authorize this work.

**Goal:** Publish the learner and producer portals over HTTPS on separate approved hostnames.
**Architecture:** Same Django/SQLite production app; host routing and role checks, host-only cookies, private read-only preview; existing Traefik Docker provider and Let’s Encrypt. Compose override; homologation stays tunnel-only.
**Tech Stack:** Django 5.2.19, Gunicorn, WhiteNoise, Docker Compose, Traefik v3.6.
**Spec:** `docs/superpowers/specs/2026-11-17-public-portals.md`.

## Global constraints
- Preserve all local changes, D01–D04, production data/keys, unrelated services and the private homologation.
- Only the two approved DNS hosts; no apex/www/email changes, no billing, no global proxy restart.
- No secrets in reports/logs/source; no real school/student data invented.
- TLS required publicly, no wildcard cookies/hosts or public Gunicorn port.

## Review focus
- Query parameters and next URLs cannot switch portals or produce external redirects.
- Wrong-role credentials/session cannot enter the other portal; CSRF remains enforced.
- Valid read-only member preview still works inside the producer host; forged preview does not bypass checks.
- Password reset/first access and private materials keep their role scope and protection.
- Healthchecks work over internal HTTP without weakening HTTPS on public routes.

## Tasks
- [x] Write failing routing/login/role/preview/settings tests; run targeted RED.
- [x] Implement host middleware, scoped authentication/reset, HTTPS settings and healthcheck; targeted GREEN, then full suite and migration check.
- [x] Add Compose override and documentation; independent whole-change review, address material findings.
- [x] Build locally, verify source, transfer immutable release/image, stage with homologation data and run remote checks.
- [x] Back up production with writers stopped; deploy only own services/router, verify real certificates and HTTP redirects, login and material privacy; retain rollback and update operations report.

## Execution
Completed 17/11/2026. Active release `20261117T202202Z`; 392 tests passed. Real Chrome login and TLS validated on both hosts. See `docs/relatorio-publicacao-https.md`.
