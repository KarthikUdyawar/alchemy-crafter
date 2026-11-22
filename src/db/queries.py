"""DB helper functions — all queries live here."""

from src.db.connection import get_connection

# ── Elements ──────────────────────────────────────────────────────────────────


def element_exists(name: str) -> bool:
    """Return True if the element is already in the DB."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM elements WHERE name = %s", (name,))
        return cur.fetchone() is not None


def save_element(name: str) -> bool:
    """
    Insert element if it doesn't exist.

    Returns True if newly inserted, False if it already existed.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO elements (name) VALUES (%s) ON CONFLICT DO NOTHING",
                (name,),
            )
            inserted = cur.rowcount == 1
        conn.commit()
    return inserted


def get_all_elements() -> list[str]:
    """Return every known element name, ordered by discovery."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT name FROM elements ORDER BY id")
        return [row[0] for row in cur.fetchall()]


# ── Recipes ───────────────────────────────────────────────────────────────────


def get_recipe(a: str, b: str) -> str | None:
    """
    Look up a recipe. Inputs are assumed already normalised (sorted).

    Returns the result element name or None.
    """
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT result FROM recipes WHERE element_a = %s AND element_b = %s",
            (a, b),
        )
        row = cur.fetchone()
        return row[0] if row else None


def save_recipe(a: str, b: str, result: str) -> bool:
    """
    Persist a recipe. Inputs are assumed already normalised (sorted).

    Returns True if newly inserted, False if it already existed.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO recipes (element_a, element_b, result)
                VALUES (%s, %s, %s)
                ON CONFLICT (element_a, element_b) DO NOTHING
                """,
                (a, b, result),
            )
            inserted = cur.rowcount == 1
        conn.commit()
    return inserted


def get_all_recipes() -> list[dict[str, str]]:
    """Return all known recipes as a list of dicts (for debugging / stats)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT element_a, element_b, result
                FROM recipes
                ORDER BY element_a, element_b
            """)
            rows = cur.fetchall()

        return [
            {
                "element_a": r[0],
                "element_b": r[1],
                "result": r[2],
            }
            for r in rows
        ]


# ── Discovered ────────────────────────────────────────────────────────────────


def get_discovered() -> list[str]:
    """Return the elements the player has discovered, ordered by discovery."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT name FROM discovered ORDER BY id")
        return [row[0] for row in cur.fetchall()]


def mark_discovered(name: str) -> None:
    """Record an element as discovered. Idempotent."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO discovered (name) VALUES (%s) ON CONFLICT DO NOTHING",
                (name,),
            )
        conn.commit()
