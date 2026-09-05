"""
Database connection pool — graceful when unavailable.

If DATABASE_URL is not set or the database is unreachable, the pool
reports ``available = False`` and every ``get_connection()`` context
manager yields ``None``.  The AI pipeline continues to function
without persistence.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    import psycopg2
    import psycopg2.pool
    HAS_PSYCOPG2 = True
except ImportError:
    psycopg2 = None  # type: ignore[assignment]
    HAS_PSYCOPG2 = False


class DatabasePool:
    """Thin wrapper around psycopg2's SimpleConnectionPool."""

    def __init__(self) -> None:
        self._pool = None
        self._available = False

    # ── lifecycle ──────────────────────────────────────────────────

    def initialize(self) -> None:
        """Try to create the connection pool.  Never raises."""
        if not HAS_PSYCOPG2:
            logger.warning(
                "psycopg2 not installed — database persistence disabled. "
                "Install with: pip install psycopg2-binary"
            )
            return

        db_url = settings.database_url
        if not db_url:
            logger.warning(
                "DATABASE_URL not set — database persistence disabled"
            )
            return

        try:
            self._pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=5,
                dsn=db_url,
            )
            # Quick connectivity check
            conn = self._pool.getconn()
            conn.cursor().execute("SELECT 1")
            self._pool.putconn(conn)

            self._available = True
            logger.info("Database connection pool initialised (%s)", db_url.split("@")[-1])
        except Exception as exc:
            logger.warning("Database connection failed — persistence disabled: %s", exc)
            self._pool = None

    def close(self) -> None:
        if self._pool is not None:
            self._pool.closeall()
            self._pool = None
        self._available = False

    # ── access ─────────────────────────────────────────────────────

    @property
    def available(self) -> bool:
        return self._available

    @contextmanager
    def get_connection(self) -> Generator:
        """
        Yield a psycopg2 connection, or ``None`` if the pool is
        unavailable.  The caller must handle ``None`` gracefully.
        """
        if not self._available or self._pool is None:
            yield None
            return

        conn = self._pool.getconn()
        try:
            yield conn
        finally:
            self._pool.putconn(conn)


# Module-level singleton
db_pool = DatabasePool()
