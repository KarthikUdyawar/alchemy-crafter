"""🎮 Phase 7 — CLI game loop with full experience polish."""

from src.cache import get_fail_count
from src.combine import combine
from src.game.display import (
    banner,
    show_elements,
    show_error,
    show_help,
    show_hint,
    show_milestone,
    show_result,
    show_session_summary,
    show_stats,
    show_streak,
)
from src.game.state import GameState
from src.validation import ValidationError, validate_inputs

HINT_THRESHOLD = 3
COMBINE_ARITY = 2
MIN_STREAK_TO_SHOW = 2


def _hint_for(a: str, b: str) -> str:
    suggestions = {
        frozenset(["fire", "water"]): "steam or mist",
        frozenset(["earth", "water"]): "mud or swamp",
        frozenset(["fire", "earth"]): "lava or magma",
        frozenset(["air", "water"]): "rain or mist",
        frozenset(["fire", "air"]): "smoke or wind",
        frozenset(["earth", "air"]): "dust or sand",
    }
    return suggestions.get(frozenset([a, b]), "keep experimenting!")


def run_cli() -> None:
    banner()

    state = GameState()
    state.load()

    print(f"  Elements known: {len(state.discovered)}")
    print("  Type 'help' for commands.\n")

    while True:
        try:
            raw = input("  ⚗️  > ").strip()
        except (KeyboardInterrupt, EOFError):
            _exit(state)
            break

        if not raw:
            continue

        tokens = raw.lower().split()
        cmd = tokens[0]

        # ── Commands ──────────────────────────────────────────────────────────
        if cmd in ("quit", "exit", "q"):
            _exit(state)
            break

        if cmd in ("help", "h", "?"):
            show_help()
            continue

        if cmd in ("list", "ls", "elements"):
            show_elements(state.discovered)
            continue

        if cmd in ("stats", "score"):
            show_stats(state.stats)
            continue

        # ── Combine ───────────────────────────────────────────────────────────
        parts = tokens[1:] if cmd == "combine" else tokens
        if len(parts) != COMBINE_ARITY:
            show_error("Need exactly 2 elements.  e.g.  fire water")
            continue

        a_raw, b_raw = parts

        try:
            result = combine(a_raw, b_raw)
        except ValidationError as e:
            show_error(str(e))

            try:
                a_n, b_n = validate_inputs(a_raw, b_raw)
                if get_fail_count(a_n, b_n) >= HINT_THRESHOLD:
                    show_hint(f"Hint for {a_n} + {b_n}: {_hint_for(a_n, b_n)}")
            except ValidationError:
                pass
            continue

        state.record_combine(result.result, result.is_new)
        show_result(a_raw, b_raw, result.result, result.is_new, result.source)

        # Streak feedback
        if result.is_new and state.discovery_streak >= MIN_STREAK_TO_SHOW:
            show_streak(state.discovery_streak)

        # Milestone check
        milestone = state.check_milestone()
        if milestone:
            show_milestone(milestone)

        # Periodic stats every 10 combines
        if state.session_combines % 10 == 0:
            show_stats(state.stats)


def _exit(state: GameState) -> None:
    if state.session_combines > 0:
        show_session_summary(state.session_summary)
    else:
        print("\n  👋  See you next time!\n")
