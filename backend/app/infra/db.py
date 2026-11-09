"""
Minimal PostgreSQL access layer over libpq (ctypes).

Why not psycopg: the build environment for slice 01 had no package-registry
access (see docs/ADR/0002-runtime-stack-under-constraint.md). libpq ships
with every PostgreSQL client install, so this layer works with nothing but
the standard library. The public surface is deliberately tiny —
`connect()`, `Connection.query()`, `Connection.transaction()` — so swapping
in psycopg 3 later touches only this file.

Parameters are always sent out-of-band via PQexecParams ($1, $2, ...).
SQL strings are never built from user input.
"""
from __future__ import annotations

import ctypes
import ctypes.util
import datetime as _dt
import decimal
import json
import uuid
from contextlib import contextmanager
from typing import Any, Iterator, Sequence

_lib_path = ctypes.util.find_library("pq") or "libpq.so.5"
_pq = ctypes.CDLL(_lib_path)

_pq.PQconnectdb.restype = ctypes.c_void_p
_pq.PQconnectdb.argtypes = [ctypes.c_char_p]
_pq.PQstatus.argtypes = [ctypes.c_void_p]
_pq.PQerrorMessage.restype = ctypes.c_char_p
_pq.PQerrorMessage.argtypes = [ctypes.c_void_p]
_pq.PQfinish.argtypes = [ctypes.c_void_p]
_pq.PQexecParams.restype = ctypes.c_void_p
_pq.PQexecParams.argtypes = [
    ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_char_p), ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int,
]
_pq.PQexec.restype = ctypes.c_void_p
_pq.PQexec.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
_pq.PQresultStatus.argtypes = [ctypes.c_void_p]
_pq.PQresultErrorMessage.restype = ctypes.c_char_p
_pq.PQresultErrorMessage.argtypes = [ctypes.c_void_p]
_pq.PQresultErrorField.restype = ctypes.c_char_p
_pq.PQresultErrorField.argtypes = [ctypes.c_void_p, ctypes.c_int]
_pq.PQntuples.argtypes = [ctypes.c_void_p]
_pq.PQnfields.argtypes = [ctypes.c_void_p]
_pq.PQfname.restype = ctypes.c_char_p
_pq.PQfname.argtypes = [ctypes.c_void_p, ctypes.c_int]
_pq.PQftype.restype = ctypes.c_uint
_pq.PQftype.argtypes = [ctypes.c_void_p, ctypes.c_int]
_pq.PQgetvalue.restype = ctypes.c_char_p
_pq.PQgetvalue.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
_pq.PQgetisnull.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
_pq.PQclear.argtypes = [ctypes.c_void_p]
_pq.PQcmdTuples.restype = ctypes.c_char_p
_pq.PQcmdTuples.argtypes = [ctypes.c_void_p]
_pq.PQtransactionStatus.argtypes = [ctypes.c_void_p]

_CONNECTION_OK = 0
_PGRES_COMMAND_OK = 1
_PGRES_TUPLES_OK = 2
_PG_DIAG_SQLSTATE = ord("C")


class DatabaseError(Exception):
    def __init__(self, message: str, sqlstate: str | None = None):
        super().__init__(message)
        self.sqlstate = sqlstate


# ── type conversion ─────────────────────────────────────────────────────────

def _parse_array(text: str) -> list[str | None]:
    """Parse a one-dimensional PostgreSQL array literal ({a,"b c",NULL})."""
    inner = text[1:-1]
    out: list[str | None] = []
    if not inner:
        return out
    buf, quoted, was_quoted, i = [], False, False, 0
    while i < len(inner):
        ch = inner[i]
        if quoted:
            if ch == "\\":
                i += 1
                buf.append(inner[i])
            elif ch == '"':
                quoted = False
            else:
                buf.append(ch)
        elif ch == '"':
            quoted = was_quoted = True
        elif ch == ",":
            val = "".join(buf)
            out.append(None if (val == "NULL" and not was_quoted) else val)
            buf, was_quoted = [], False
        else:
            buf.append(ch)
        i += 1
    val = "".join(buf)
    out.append(None if (val == "NULL" and not was_quoted) else val)
    return out


_SCALAR = {
    16: lambda s: s == "t",
    20: int, 21: int, 23: int, 26: int,
    700: float, 701: float,
    1700: decimal.Decimal,
    2950: uuid.UUID,
    1082: _dt.date.fromisoformat,
    1184: lambda s: _dt.datetime.fromisoformat(s if len(s) > 22 and s[-3] == ":" else s + ":00"),
    1114: _dt.datetime.fromisoformat,
    114: json.loads, 3802: json.loads,
}
_ARRAY_ELEM = {1009: str, 1015: str, 2951: uuid.UUID, 1007: int, 1005: int, 1016: int, 1000: lambda s: s == "t"}


def _convert(oid: int, raw: str) -> Any:
    if oid in _SCALAR:
        return _SCALAR[oid](raw)
    if oid in _ARRAY_ELEM:
        f = _ARRAY_ELEM[oid]
        return [None if v is None else f(v) for v in _parse_array(raw)]
    return raw


def _array_literal(items: Sequence[Any]) -> str:
    parts = []
    for v in items:
        if v is None:
            parts.append("NULL")
        else:
            s = str(v).replace("\\", "\\\\").replace('"', '\\"')
            parts.append(f'"{s}"')
    return "{" + ",".join(parts) + "}"


def _to_param(v: Any) -> bytes | None:
    if v is None:
        return None
    if isinstance(v, bool):
        return b"true" if v else b"false"
    if isinstance(v, (dict,)):
        return json.dumps(v, default=str, sort_keys=True).encode()
    if isinstance(v, (list, tuple)):
        return _array_literal(v).encode()
    if isinstance(v, (_dt.date, _dt.datetime)):
        return v.isoformat().encode()
    return str(v).encode()


# ── connection ──────────────────────────────────────────────────────────────

class Connection:
    def __init__(self, dsn: str):
        self._conn = _pq.PQconnectdb(dsn.encode())
        if not self._conn or _pq.PQstatus(self._conn) != _CONNECTION_OK:
            msg = _pq.PQerrorMessage(self._conn).decode(errors="replace") if self._conn else "connect failed"
            if self._conn:
                _pq.PQfinish(self._conn)
                self._conn = None
            raise DatabaseError(msg.strip())

    def close(self) -> None:
        if self._conn:
            _pq.PQfinish(self._conn)
            self._conn = None

    def __enter__(self) -> "Connection":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def execute_script(self, sql: str) -> None:
        """Run a multi-statement script (migrations only — no parameters)."""
        res = _pq.PQexec(self._conn, sql.encode())
        self._check(res, keep=False)

    def query(self, sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
        names, rows, _ = self.query_rows(sql, params)
        return [dict(zip(names, r)) for r in rows]

    def query_rows(self, sql: str, params: Sequence[Any] | None = ()) -> tuple[list[str], list[tuple], int]:
        """Column names, rows as tuples (column order kept, duplicates allowed)
        and the affected-row count. params=None sends the text with the simple
        query protocol (several statements allowed; the last result is read)."""
        if params is None:
            res = _pq.PQexec(self._conn, sql.encode())
        else:
            n = len(params)
            values = (ctypes.c_char_p * max(n, 1))(*[_to_param(p) for p in params]) if n else None
            res = _pq.PQexecParams(self._conn, sql.encode(), n, None, values, None, None, 0)
        self._check(res, keep=True)
        try:
            nrows, cols = _pq.PQntuples(res), _pq.PQnfields(res)
            names = [_pq.PQfname(res, c).decode() for c in range(cols)]
            types = [_pq.PQftype(res, c) for c in range(cols)]
            rows = [tuple(None if _pq.PQgetisnull(res, r, c)
                          else _convert(types[c], _pq.PQgetvalue(res, r, c).decode()) for c in range(cols))
                    for r in range(nrows)]
            affected = _pq.PQcmdTuples(res).decode()
            return names, rows, int(affected) if affected else (nrows if cols else -1)
        finally:
            _pq.PQclear(res)

    def transaction_status(self) -> int:
        """libpq PQtransactionStatus: 0 idle, 1 active, 2 in transaction, 3 in failed transaction."""
        return _pq.PQtransactionStatus(self._conn)

    def one(self, sql: str, params: Sequence[Any] = ()) -> dict[str, Any] | None:
        rows = self.query(sql, params)
        return rows[0] if rows else None

    @contextmanager
    def transaction(self) -> Iterator["Connection"]:
        self.query("BEGIN")
        try:
            yield self
        except BaseException:
            self.query("ROLLBACK")
            raise
        else:
            self.query("COMMIT")

    def _check(self, res: int | None, keep: bool) -> None:
        if not res:
            raise DatabaseError(_pq.PQerrorMessage(self._conn).decode(errors="replace"))
        status = _pq.PQresultStatus(res)
        if status not in (_PGRES_COMMAND_OK, _PGRES_TUPLES_OK):
            msg = _pq.PQresultErrorMessage(res).decode(errors="replace").strip()
            state = _pq.PQresultErrorField(res, _PG_DIAG_SQLSTATE)
            _pq.PQclear(res)
            raise DatabaseError(msg, state.decode() if state else None)
        if not keep:
            _pq.PQclear(res)


def connect(dsn: str) -> Connection:
    return Connection(dsn)


@contextmanager
def tenant_transaction(dsn: str, tenant_id: uuid.UUID | str | None) -> Iterator[Connection]:
    """One connection + one transaction with the RLS tenant context set
    transaction-locally. When tenant_id is None the context stays unset and
    every tenant-scoped table reads as empty (fail closed)."""
    with connect(dsn) as conn, conn.transaction():
        if tenant_id is not None:
            conn.query("SELECT set_config('vetbuddy.tenant_id', $1, true)", [str(tenant_id)])
        yield conn
