# Alchemy Crafter — Sprint 2: Gameplay Loop, Reliability, Quality Gate

**Duration:** Week 2 (Days 8–14)
**Goal:** Playable end-to-end game with persistent progress, race-safe AI path, CI on every PR.
**Branch strategy:** `develop` base → feature branches → PR → CodeRabbit review → merge
**Method:** TDD. One failing test → minimal code → repeat. Public interfaces only

## Sprint Goal
>
> Player resumes saved game, combines only discovered elements, gets AI results fast on warm model, and every PR passes lint + tests in CI.

---

## Backlog

### 🧾 DOC-1 — Reconcile docs with code

**Branch:** `chore/docs-sync`

- [ ] SPRINT_1 lists CLI/API/tests as out of scope but they exist → add "shipped" note
- [ ] Fix test count (85+ vs ~100) from `pytest --collect-only`
- [ ] Fix ARCHITECTURE.md links (`./docs/PRD.md` → `./PRD.md`)
- [ ] API.md: document 404 unknown element, or drop it from flow diagrams
- [ ] Resolve AI target (<2s) vs `OLLAMA_TIMEOUT` (100s)

### 🎮 PLAY-1 — Player progress

**Branch:** `feature/player-progress`

- [ ] RED: combine rejects undiscovered element; discoveries survive restart
- [ ] `discovered` table + `mark_discovered`, `get_discovered`; seed 4 base
- [ ] `combine()` requires discovered inputs; marks result discovered
- [ ] CLI `list` reads discovered; `GET /elements` stays global
- [ ] Skip: player ids, `player:<id>:discovered` Redis set (single-player, YAGNI)

### 🔒 RACE-1 — Lock & concurrency

**Branch:** `fix/generation-race`

- [ ] RED: 2 concurrent `combine(a, b)` → 1 Ollama call, same result, one `is_new: true`
- [ ] Lock = `SET NX PX` + token; release only if token matches
- [ ] Lock loser polls cache/DB, never calls Ollama
- [ ] `save_recipe`: `ON CONFLICT DO NOTHING`, re-read winner
- [ ] `fail:` counters: wire into backoff or delete

### 🤖 AI-2 — Latency & output quality

**Branch:** `feature/ai-latency`

- [ ] Measure first: p50/p95 per model, cold vs warm; record in ARCHITECTURE.md
- [ ] Ollama `keep_alive`, small `num_predict`, low temperature; warm-up on boot
- [ ] Reject result equal to either input
- [ ] Prompt guard: cap/sanitise element names before interpolation

### 🛡️ QA-1 — Quality gate

**Branch:** `chore/ci`

- [ ] GitHub Actions: `ruff`, `pytest -m unit`; integration job with Postgres/Redis services
- [ ] Coverage report, floor = current baseline
- [ ] Review pass: `combine.py`, `generator.py`, `queries.py` (security/perf/correctness)

### 📊 OBS-1 — Success metrics

**Branch:** `feature/stats`

- [ ] RED: `GET /stats` returns cache/db/ai counts + hit ratio
- [ ] Redis counters incremented in `combine()`

---

## Definition of Done

- [ ] All branches merged to `develop`, CI green
- [ ] `docker compose up` smoke: restart keeps progress
- [ ] SPRINT_2.md checked off, moved to `docs/`

---

## Out of Scope (→ Sprint 3)

- Web UI, auth, multiplayer, achievements, hints, daily challenges

## Open Questions (verify from code before starting)

- Does `combine()` already enforce discovered-only / 404?
- Does lock code exist? Sync psycopg2 inside async routes?
