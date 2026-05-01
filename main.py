"""
🧪 Alchemy Crafter — Main Entry Point
Run with: uv run main.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.logger import setup_logging
from src.config import config
from src.logger import get_logger

setup_logging()  # must be first before any src imports

log = get_logger("main")


def check_services() -> list:
    issues = []

    try:
        import redis

        r = redis.from_url(config.REDIS_URL, socket_connect_timeout=2)
        r.ping()
        print("  ✅ Redis connected")
    except Exception as e:
        print(f"  ❌ Redis: {e}")
        log.error("Redis unavailable: %s", e)
        issues.append("Redis")

    try:
        import psycopg2

        conn = psycopg2.connect(config.DATABASE_URL, connect_timeout=3)
        conn.close()
        print("  ✅ PostgreSQL connected")
    except Exception as e:
        print(f"  ❌ PostgreSQL: {e}")
        log.error("PostgreSQL unavailable: %s", e)
        issues.append("PostgreSQL")

    try:
        import httpx

        resp = httpx.get(f"{config.OLLAMA_URL}/api/tags", timeout=3)
        resp.raise_for_status()
        print("  ✅ Ollama connected")
    except Exception as e:
        print(f"  ❌ Ollama: {e}")
        log.error("Ollama unavailable: %s", e)
        issues.append("Ollama")

    return issues


def main():
    print("🧪 Alchemy Crafter")
    print("=" * 40)
    print("Checking services...")
    issues = check_services()

    if issues:
        print(f"\n⚠️  Services not ready: {', '.join(issues)}")
        print("   Please check your .env and start required services.")
        print("   See .env.example for configuration.")
        sys.exit(1)

    print("\nAll services ready.")

    from src.db import init_db

    init_db()

    print("Starting game...\n")
    from src.game.cli import run_cli

    run_cli()


if __name__ == "__main__":
    main()
