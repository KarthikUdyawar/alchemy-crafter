# Alchemy Crafter — Sprint 2: TODO

Scope: [PRD.md](PRD.md). Decisions: [DECISION.md](../../DECISION.md).

## Backlog

### 🧾 DOC-1 — Reconcile docs with code

- [x] SPRINT_1 lists CLI/API/tests as out of scope but they exist → add "shipped" note
- [x] Fix test count (85+ vs ~100) from `pytest --collect-only`
- [x] Fix ARCHITECTURE.md links (`./docs/PRD.md` → `./ROADMAP.md`)
- [x] API.md: document 404 unknown element, or drop it from flow diagrams
- [ ] Resolve AI target (<2s) vs `OLLAMA_TIMEOUT` (100s)

### 🎮 PLAY-1 — Player progress

- [ ] RED: combine rejects undiscovered element; discoveries survive restart
- [ ] `discovered` table + `mark_discovered`, `get_discovered`; seed 4 base
- [ ] `combine()` requires discovered inputs; marks result discovered
- [ ] CLI `list` reads discovered; `GET /elements` stays global
- [ ] Skip: player ids, `player:<id>:discovered` Redis set (single-player, YAGNI)

### 🔒 RACE-1 — Lock & concurrency

- [ ] RED: 2 concurrent `combine(a, b)` → 1 Ollama call, same result, one `is_new: true`
- [ ] Lock = `SET NX PX` + token; release only if token matches
- [ ] Lock loser polls cache/DB, never calls Ollama
- [ ] `save_recipe`: `ON CONFLICT DO NOTHING`, re-read winner
- [ ] `fail:` counters: wire into backoff or delete

### 🤖 AI-2 — Latency & output quality

- [ ] Measure first: p50/p95 per model, cold vs warm; record in ARCHITECTURE.md
- [ ] Ollama `keep_alive`, small `num_predict`, low temperature; warm-up on boot
- [ ] Reject result equal to either input
- [ ] Prompt guard: cap/sanitise element names before interpolation

### 🛡️ QA-1 — Quality gate

- [ ] GitHub Actions: `ruff`, `pytest -m unit`; integration job with Postgres/Redis services
- [x] Coverage report, floor = current baseline
- [ ] Review pass: `combine.py`, `generator.py`, `queries.py` (security/perf/correctness)

### 📊 OBS-1 — Success metrics

- [ ] RED: `GET /stats` returns cache/db/ai counts + hit ratio
- [ ] Redis counters incremented in `combine()`

---

## Definition of Done

- [ ] Sprint branch merged to `master`, CI green
- [ ] `docker compose up` smoke: restart keeps progress
- [ ] TODO.md checked off
