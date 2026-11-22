# Alchemy Crafter — Sprint 2: Gameplay Loop, Reliability, Quality Gate

**Duration:** Week 2 (Days 8–14)
**Branch:** `feature/qa-tooling` for the whole sprint ([D-007](../../DECISION.md))
**Method:** TDD. One failing test → minimal code → repeat. Public interfaces only.

## Goal

> Player resumes saved game, combines only discovered elements, gets AI results fast on warm
> model, and every PR passes lint + tests in CI.

Tasks: [TODO.md](TODO.md).

## Out of Scope (→ Sprint 3)

- Web UI, auth, multiplayer, achievements, hints, daily challenges

## Open Questions

Answered from code (see "Known deviations" in [CLAUDE.md](../../../CLAUDE.md)):

- `combine()` does not enforce discovered-only or the 404 check. The API route does the 404 check.
- The lock lives in `src/api/routes.py`, not in `combine()`. The CLI bypasses it.
- Routes are `async def` but call blocking psycopg2 and sync `httpx`.
