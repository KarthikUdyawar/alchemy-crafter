"""Game state — session tracking, milestones, streaks."""

from src.db import get_all_elements

# Discovery count milestones → message
MILESTONES: list[tuple[int, str]] = [
    (10, "Apprentice Alchemist 🌱"),
    (25, "Journeyman Alchemist ⚗️"),
    (50, "Expert Alchemist 🔥"),
    (100, "Master Alchemist 🌟"),
    (200, "Grand Alchemist 🧙"),
]


class GameState:
    def __init__(self) -> None:
        self.discovered: set[str] = set()
        self.session_new: int = 0
        self.session_combines: int = 0
        self.discovery_streak: int = 0  # consecutive new discoveries
        self.best_streak: int = 0
        self._milestones_hit: set[int] = set()

    def load(self) -> None:
        self.discovered = set(get_all_elements())

    def record_combine(self, result: str, is_new: bool) -> None:
        self.discovered.add(result)
        self.session_combines += 1
        if is_new:
            self.session_new += 1
            self.discovery_streak += 1
            self.best_streak = max(self.best_streak, self.discovery_streak)
        else:
            self.discovery_streak = 0

    def check_milestone(self) -> str | None:
        """Return milestone message if just crossed one, else None."""
        total = len(self.discovered)
        for threshold, msg in MILESTONES:
            if threshold <= total and threshold not in self._milestones_hit:
                self._milestones_hit.add(threshold)
                return msg
        return None

    @property
    def stats(self) -> str:
        streak = f"  streak: {self.discovery_streak}" if self.discovery_streak > 1 else ""
        return (
            f"elements: {len(self.discovered)}  |  "
            f"combines: {self.session_combines}  |  "
            f"new: {self.session_new}"
            f"{streak}"
        )

    @property
    def session_summary(self) -> list[str]:
        lines = [
            f"  Combines this session : {self.session_combines}",
            f"  New discoveries       : {self.session_new}",
            f"  Total elements known  : {len(self.discovered)}",
        ]
        if self.best_streak > 1:
            lines.append(f"  Best discovery streak : {self.best_streak} 🔥")
        return lines
