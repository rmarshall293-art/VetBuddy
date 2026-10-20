"""Database access with per-transaction tenant context.

Every request that touches protected data runs inside `scoped(principal)`: one
transaction on the least-privilege login with app.tenant_id / app.user_id set
LOCAL, so the context dies with the transaction and pooled connections never
carry it to the next caller. RLS does the filtering; this module never adds
tenant WHERE clauses of its own.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


class Database:
    def __init__(self, url: str, min_size: int = 1, max_size: int = 10):
        self.pool = ConnectionPool(url, min_size=min_size, max_size=max_size, open=True,
                                   kwargs={"row_factory": dict_row, "autocommit": False})

    def close(self) -> None:
        self.pool.close()

    def ping(self) -> bool:
        try:
            with self.pool.connection(timeout=2) as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    @contextmanager
    def unscoped(self) -> Iterator[psycopg.Connection]:
        """A transaction with no tenant context: protected tables read as empty."""
        with self.pool.connection() as conn:
            with conn.transaction():
                yield conn

    @contextmanager
    def scoped(self, tenant_id: str, user_id: str) -> Iterator[psycopg.Connection]:
        with self.pool.connection() as conn:
            with conn.transaction():
                conn.execute("SELECT set_config('app.tenant_id', %s, true), set_config('app.user_id', %s, true)",
                             (str(tenant_id), str(user_id)))
                yield conn
