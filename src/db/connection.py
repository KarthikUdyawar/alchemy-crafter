"""DB connection — auto-reconnect + retry on transient errors."""

import time

import psycopg2
import psycopg2.extensions
import psycopg2.extras

from src.config import config
from src.logger import get_logger

log = get_logger("db")

_RETRY_ATTEMPTS = 3
_RETRY_DELAY = 0.5  # seconds


def get_connection() -> psycopg2.extensions.connection:
    """Return a new psycopg2 connection, retrying on failure."""
    last_err: psycopg2.OperationalError | None = None
    for attempt in range(1, _RETRY_ATTEMPTS + 1):
        try:
            return psycopg2.connect(config.DATABASE_URL)
        except psycopg2.OperationalError as e:
            last_err = e
            log.warning("DB connect attempt %d/%d failed: %s", attempt, _RETRY_ATTEMPTS, e)
            if attempt < _RETRY_ATTEMPTS:
                time.sleep(_RETRY_DELAY * attempt)
    if last_err is None:
        raise RuntimeError("no DB connection attempts were made")
    raise last_err


def init_db() -> None:
    """Create tables and seed base elements if they don't exist."""
    ddl = """
    CREATE TABLE IF NOT EXISTS elements (
        id         SERIAL PRIMARY KEY,
        name       TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS recipes (
        id         SERIAL PRIMARY KEY,
        element_a  TEXT NOT NULL,
        element_b  TEXT NOT NULL,
        result     TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT NOW(),
        UNIQUE (element_a, element_b)
    );

    CREATE TABLE IF NOT EXISTS discovered (
        id         SERIAL PRIMARY KEY,
        name       TEXT UNIQUE NOT NULL REFERENCES elements (name),
        created_at TIMESTAMP DEFAULT NOW()
    );
    """
    base_elements = ["fire", "water", "earth", "air"]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
            for el in base_elements:
                cur.execute(
                    "INSERT INTO elements (name) VALUES (%s) ON CONFLICT DO NOTHING",
                    (el,),
                )
            # Single-player: every known element is discovered. Also keeps old databases playable.
            cur.execute(
                "INSERT INTO discovered (name) SELECT name FROM elements ORDER BY id "
                "ON CONFLICT DO NOTHING"
            )
        conn.commit()

    log.info("DB initialised — base elements seeded")
    print(f"  ✅ DB ready — base elements: {', '.join(base_elements)}")
