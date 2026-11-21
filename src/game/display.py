"""Terminal output helpers — colours, banners, all feedback."""

import shutil

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_GOLD = "\033[33m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[93m"
_PURPLE = "\033[35m"

_STREAK_DOUBLE = 2
_STREAK_TRIPLE = 3
_STREAK_ON_FIRE = 5


def _w(text: str, colour: str) -> str:
    return f"{colour}{text}{_RESET}"


def _width() -> int:
    return min(shutil.get_terminal_size().columns, 60)


def banner() -> None:
    w = _width()
    print(_w("━" * w, _GOLD))
    print(_w("  🧪  A L C H E M Y   C R A F T E R", _BOLD + _GOLD))
    print(_w("━" * w, _GOLD))
    print(_w("  Combine elements. Discover the world.", _DIM))
    print()


def show_elements(discovered: set[str]) -> None:
    sorted_els = sorted(discovered)
    cols = 4
    print(_w(f"\n  📚 Known elements ({len(sorted_els)}):", _CYAN))
    for i, el in enumerate(sorted_els):
        end = "\n" if (i + 1) % cols == 0 else ""
        print(f"    {el:<18}", end=end)
    if len(sorted_els) % cols:
        print()
    print()


def show_result(a: str, b: str, result: str, is_new: bool, source: str) -> None:
    src_tag = _w(f"[{source}]", _DIM)
    if is_new:
        print(_w("\n  ✨ NEW DISCOVERY!", _BOLD + _GOLD))
        print(_w(f"     {a} + {b}  →  {result}", _BOLD + _GREEN) + f"  {src_tag}")
    else:
        print(_w(f"\n  ⚗️   {a} + {b}  →  {result}", _CYAN) + f"  {src_tag}")


def show_streak(streak: int) -> None:
    if streak == _STREAK_DOUBLE:
        print(_w("  🔥 2 in a row!", _YELLOW))
    elif streak == _STREAK_TRIPLE:
        print(_w("  🔥🔥 3-discovery streak!", _YELLOW))
    elif streak >= _STREAK_ON_FIRE:
        print(_w(f"  🔥🔥🔥 {streak}-discovery streak — on fire!", _BOLD + _YELLOW))


def show_milestone(msg: str) -> None:
    w = _width()
    print()
    print(_w("  " + "★" * ((w - 4) // 2), _GOLD))
    print(_w(f"  🏆  {msg}", _BOLD + _GOLD))
    print(_w("  " + "★" * ((w - 4) // 2), _GOLD))


def show_error(msg: str) -> None:
    print(_w(f"\n  ✗  {msg}", _RED))


def show_hint(msg: str) -> None:
    print(_w(f"\n  💡 {msg}", _YELLOW))


def show_stats(stats: str) -> None:
    print(_w(f"\n  {stats}", _DIM))


def show_session_summary(lines: list[str]) -> None:
    w = _width()
    print()
    print(_w("━" * w, _GOLD))
    print(_w("  📊  Session Summary", _BOLD + _CYAN))
    print(_w("━" * w, _GOLD))
    for line in lines:
        print(_w(line, _CYAN))
    print()


def show_help() -> None:
    print(_w("\n  Commands:", _CYAN))
    print("    <a> <b>       combine two elements  (e.g. fire water)")
    print("    list          show all known elements")
    print("    stats         session stats")
    print("    help          this message")
    print("    quit / exit   leave the game\n")
