"""
DB tests.

- Unit tests: mock psycopg2 connection, fully offline.
- Integration tests: require live Postgres (mark: integration).
"""

from unittest.mock import MagicMock

import pytest

# ── Helpers ───────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_conn(mocker):
    """
    Patch get_connection() so no real Postgres is needed.

    Returns (mock_conn, mock_cursor) for assertion access.
    """
    cur = MagicMock()
    conn = MagicMock()
    conn.__enter__ = lambda s: s
    conn.__exit__ = MagicMock(return_value=False)
    conn.cursor.return_value.__enter__ = lambda s: cur
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    mocker.patch("src.db.queries.get_connection", return_value=conn)
    mocker.patch("src.db.connection.get_connection", return_value=conn)
    return conn, cur


# ── Unit: queries ─────────────────────────────────────────────────────────────


class TestElementQueriesUnit:
    @pytest.mark.unit
    def test_element_exists_true(self, mock_conn):
        from src.db.queries import element_exists

        _, cur = mock_conn
        cur.fetchone.return_value = (1,)
        assert element_exists("fire") is True
        cur.execute.assert_called_once()
        assert "fire" in cur.execute.call_args[0][1]

    @pytest.mark.unit
    def test_element_exists_false(self, mock_conn):
        from src.db.queries import element_exists

        _, cur = mock_conn
        cur.fetchone.return_value = None
        assert element_exists("__ghost__") is False

    @pytest.mark.unit
    def test_save_element_new(self, mock_conn):
        from src.db.queries import save_element

        conn, cur = mock_conn
        cur.rowcount = 1
        assert save_element("steam") is True
        conn.commit.assert_called_once()

    @pytest.mark.unit
    def test_save_element_duplicate(self, mock_conn):
        from src.db.queries import save_element

        _, cur = mock_conn
        cur.rowcount = 0
        assert save_element("fire") is False

    @pytest.mark.unit
    def test_get_all_elements(self, mock_conn):
        from src.db.queries import get_all_elements

        _, cur = mock_conn
        cur.fetchall.return_value = [("fire",), ("water",), ("steam",)]
        result = get_all_elements()
        assert result == ["fire", "water", "steam"]


class TestRecipeQueriesUnit:
    @pytest.mark.unit
    def test_get_recipe_hit(self, mock_conn):
        from src.db.queries import get_recipe

        _, cur = mock_conn
        cur.fetchone.return_value = ("steam",)
        assert get_recipe("fire", "water") == "steam"

    @pytest.mark.unit
    def test_get_recipe_miss(self, mock_conn):
        from src.db.queries import get_recipe

        _, cur = mock_conn
        cur.fetchone.return_value = None
        assert get_recipe("lead", "gold") is None

    @pytest.mark.unit
    def test_save_recipe_new(self, mock_conn):
        from src.db.queries import save_recipe

        conn, cur = mock_conn
        cur.rowcount = 1
        assert save_recipe("fire", "water", "steam") is True
        conn.commit.assert_called_once()

    @pytest.mark.unit
    def test_save_recipe_duplicate(self, mock_conn):
        from src.db.queries import save_recipe

        _, cur = mock_conn
        cur.rowcount = 0
        assert save_recipe("fire", "water", "steam") is False

    @pytest.mark.unit
    def test_get_all_recipes(self, mock_conn):
        from src.db.queries import get_all_recipes

        _, cur = mock_conn
        cur.fetchall.return_value = [("fire", "water", "steam")]
        result = get_all_recipes()
        assert result == [{"element_a": "fire", "element_b": "water", "result": "steam"}]


# ── Integration tests (live Postgres) ─────────────────────────────────────────


class TestDbIntegration:
    @pytest.fixture(autouse=True)
    def skip_if_no_db(self):
        try:
            from src.db.connection import get_connection

            conn = get_connection()
            conn.close()
        except Exception as e:
            pytest.skip(f"Postgres not available: {e}")

    @pytest.mark.integration
    def test_init_seeds_base_elements(self):
        from src.db import get_all_elements, init_db

        init_db()
        elements = get_all_elements()
        for base in ("fire", "water", "earth", "air"):
            assert base in elements

    @pytest.mark.integration
    def test_element_exists(self):
        from src.db import element_exists

        assert element_exists("fire")
        assert not element_exists("__nonexistent_xyz__")

    @pytest.mark.integration
    def test_save_element_idempotent(self):
        from src.db import element_exists, save_element

        save_element("__test_steam__")
        assert element_exists("__test_steam__")
        assert save_element("__test_steam__") is False  # duplicate

    @pytest.mark.integration
    def test_recipe_roundtrip(self):
        from src.db import get_all_recipes, get_recipe, save_recipe

        save_recipe("fire", "water", "steam")
        assert get_recipe("fire", "water") == "steam"
        recipes = get_all_recipes()
        assert any(r["result"] == "steam" for r in recipes)
