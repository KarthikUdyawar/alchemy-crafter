# Alchemy Crafter — Sprint 1: Core MVP & Infrastructure

**Duration:** Week 1 (Days 1–7)

## Goal

> By the end of this sprint, developers can run the full stack locally via `docker compose up`,
> combine any two elements through the core pipeline (with Redis cache + Postgres persistence
> fallback to Ollama), and get reliable, single-word substance results with full input
> validation.

Tasks: [TODO.md](TODO.md). Decisions: [D-001 to D-005](../../DECISION.md).

## Out of Scope (→ Sprint 2)

- CLI game loop and user-facing commands
- Game experience features (streaks, milestones, session summary)
- FastAPI layer and HTTP endpoints
- Full test suite and API-specific enhancements
- Player system, achievements, or Web UI

## Shipped after Sprint 1 closed

- CLI game loop, game state, FastAPI layer and the test suite exist in the repository.
  See [ARCHITECTURE.md](../../ARCHITECTURE.md).

## Not shipped

- Player system, achievements, Web UI. Player progress is Sprint 2 PLAY-1.
