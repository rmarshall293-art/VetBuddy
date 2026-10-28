"""A psycopg 3 shaped facade over the libpq driver in ``app.infra.db``.

Why: the Benefit Vault (migration 0014) was written against psycopg 3, which
this build environment cannot install (ADR 0002: no package registry). Rather
than fork the vault's store and tests into a second database dialect, this
module offers the small part of the psycopg 3 surface they use, implemented on
the one driver the rest of the app already uses. When psycopg becomes
installable, ``connect`` here is replaced by ``psycopg.connect`` and nothing
else changes (ADR 0005).

Supported surface:

    conn = connect(conninfo, autocommit=False)   # also a context manager
    cur = conn.execute(sql, params=None)          # %s placeholders, %% for a literal %
    cur.fetchone(), cur.fetchall(), iter(cur), cur.rowcount
    with conn.transaction(): ...                  # BEGIN/COMMIT, nested -> SAVEPOINT
    raise Rollback()                              # inside a block: undo it quietly
    conn.commit(), conn.rollback(), conn.close()
    errors.CheckViolation, errors.InsufficientPrivilege, ... (by SQLSTATE)

Semantics follow psycopg 3: outside autocommit the first statement opens a
transaction; leaving ``with conn:`` commits (or rolls back on an exception)
and closes. Without parameters the text goes over the simple query protocol,
so a migration file runs as one call and ``%`` needs no escaping.
"""
from __future__ import annotations

import itertools
import types
from contextlib import contextmanager
from typing import Any, Iterator, Optional, Sequence

from . import db

# ── errors (psycopg.errors names, keyed by SQLSTATE) ─────────────────────────


class Error(db.DatabaseError):
    sqlstate: Optional[str] = None


class DatabaseError(Error):
    pass


class IntegrityError(DatabaseError):
    pass


class ProgrammingError(DatabaseError):
    pass


class DataError(DatabaseError):
    pass


class OperationalError(DatabaseError):
    pass


class InternalError(DatabaseError):
    pass


class NotSupportedError(DatabaseError):
    pass


class Rollback(Exception):
    """Raise inside ``with conn.transaction():`` to roll that block back quietly (psycopg 3)."""


_BY_STATE: dict[str, type] = {}


def _cls(name: str, base: type, state: str) -> type:
    cls = type(name, (base,), {"sqlstate": state})
    _BY_STATE[state] = cls
    return cls


errors = types.SimpleNamespace(
    Error=Error, DatabaseError=DatabaseError, IntegrityError=IntegrityError,
    ProgrammingError=ProgrammingError, DataError=DataError, OperationalError=OperationalError,
    InternalError=InternalError, NotSupportedError=NotSupportedError,
    CheckViolation=_cls("CheckViolation", IntegrityError, "23514"),
    ForeignKeyViolation=_cls("ForeignKeyViolation", IntegrityError, "23503"),
    UniqueViolation=_cls("UniqueViolation", IntegrityError, "23505"),
    NotNullViolation=_cls("NotNullViolation", IntegrityError, "23502"),
    RestrictViolation=_cls("RestrictViolation", IntegrityError, "23001"),
    InsufficientPrivilege=_cls("InsufficientPrivilege", ProgrammingError, "42501"),
    UndefinedTable=_cls("UndefinedTable", ProgrammingError, "42P01"),
    UndefinedFunction=_cls("UndefinedFunction", ProgrammingError, "42883"),
    SyntaxError=_cls("SyntaxError", ProgrammingError, "42601"),
    InvalidParameterValue=_cls("InvalidParameterValue", DataError, "22023"),
    InvalidTextRepresentation=_cls("InvalidTextRepresentation", DataError, "22P02"),
    ObjectNotInPrerequisiteState=_cls("ObjectNotInPrerequisiteState", OperationalError, "55000"),
    SerializationFailure=_cls("SerializationFailure", OperationalError, "40001"),
    RaiseException=_cls("RaiseException", InternalError, "P0001"),
    NoDataFound=_cls("NoDataFound", InternalError, "P0002"),
    FeatureNotSupported=_cls("FeatureNotSupported", NotSupportedError, "0A000"),
)


def _class_for(state: Optional[str]) -> type:
    if state in _BY_STATE:
        return _BY_STATE[state]
    prefix = (state or "")[:2]
    return {"23": IntegrityError, "42": ProgrammingError, "22": DataError, "55": OperationalError,
            "40": OperationalError, "0A": NotSupportedError}.get(prefix, DatabaseError)


def _raise(exc: db.DatabaseError) -> None:
    cls = _class_for(exc.sqlstate)
    new = cls(str(exc), exc.sqlstate)
    new.sqlstate = exc.sqlstate
    raise new from None


# ── placeholders ─────────────────────────────────────────────────────────────

def _positional(sql: str) -> str:
    """psycopg %s placeholders to libpq $n; %% becomes %. Anything else after % is refused."""
    out, n, i = [], 0, 0
    while i < len(sql):
        ch = sql[i]
        if ch == "%":
            nxt = sql[i + 1:i + 2]
            if nxt == "s":
                n += 1
                out.append(f"${n}")
            elif nxt == "%":
                out.append("%")
            else:
                raise ProgrammingError(f"unsupported placeholder %{nxt}")
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


# ── cursor and connection ────────────────────────────────────────────────────

class Cursor:
    def __init__(self, rows: list[tuple], rowcount: int, names: list[str]):
        self._rows = rows
        self._i = 0
        self.rowcount = rowcount
        self.description = [(n,) for n in names] if names else None

    def fetchone(self) -> Optional[tuple]:
        if self._i >= len(self._rows):
            return None
        row = self._rows[self._i]
        self._i += 1
        return row

    def fetchall(self) -> list[tuple]:
        rows = self._rows[self._i:]
        self._i = len(self._rows)
        return rows

    def __iter__(self) -> Iterator[tuple]:
        while True:
            row = self.fetchone()
            if row is None:
                return
            yield row


_IDLE, _INERROR = 0, 3
_sp = itertools.count(1)


class Connection:
    def __init__(self, conninfo: str, autocommit: bool = False):
        try:
            self._raw = db.connect(conninfo)
        except db.DatabaseError as exc:
            raise OperationalError(str(exc), exc.sqlstate) from None
        self.autocommit = autocommit
        self.closed = False

    # psycopg: Connection.connect(...) is the classmethod spelling
    @classmethod
    def connect(cls, conninfo: str, autocommit: bool = False) -> "Connection":
        return cls(conninfo, autocommit)

    def _status(self) -> int:
        return self._raw.transaction_status()

    def _run(self, sql: str, params: Optional[Sequence[Any]]):
        try:
            if params is None:
                return self._raw.query_rows(sql, None)
            return self._raw.query_rows(_positional(sql), list(params))
        except db.DatabaseError as exc:
            _raise(exc)

    def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> Cursor:
        if self.closed:
            raise OperationalError("the connection is closed")
        if not self.autocommit and self._status() == _IDLE:
            self._run("BEGIN", None)
        names, rows, count = self._run(sql, params)
        return Cursor(rows, count, names)

    def commit(self) -> None:
        if self._status() != _IDLE:
            self._run("COMMIT", None)

    def rollback(self) -> None:
        if self._status() != _IDLE:
            self._run("ROLLBACK", None)

    @contextmanager
    def transaction(self) -> Iterator["Connection"]:
        """Outermost block: BEGIN ... COMMIT. Inside a transaction: a savepoint."""
        if self._status() == _IDLE:
            self._run("BEGIN", None)
            try:
                yield self
            except Rollback:
                self._run("ROLLBACK", None)
            except BaseException:
                self._run("ROLLBACK", None)
                raise
            else:
                self._run("COMMIT", None)
        else:
            name = f"vb_sp_{next(_sp)}"
            self._run(f"SAVEPOINT {name}", None)
            try:
                yield self
            except Rollback:
                self._run(f"ROLLBACK TO SAVEPOINT {name}", None)
                self._run(f"RELEASE SAVEPOINT {name}", None)
            except BaseException:
                self._run(f"ROLLBACK TO SAVEPOINT {name}", None)
                self._run(f"RELEASE SAVEPOINT {name}", None)
                raise
            else:
                self._run(f"RELEASE SAVEPOINT {name}", None)

    def close(self) -> None:
        if not self.closed:
            self._raw.close()
            self.closed = True

    def __enter__(self) -> "Connection":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if not self.closed:
                if exc_type is None:
                    self.commit()
                elif self._status() != _IDLE:
                    self._run("ROLLBACK", None)
        finally:
            self.close()


def connect(conninfo: str, autocommit: bool = False) -> Connection:
    return Connection(conninfo, autocommit)
