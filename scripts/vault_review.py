#!/usr/bin/env python3
"""Benefit Vault review workflow (gate G1). Run by the project owner, against the
owner database URL (DATABASE_ADMIN_URL); the API never uses this.

  scripts/vault_review.py sync-roster                  copy config/reviewer_roster.yaml into the database
  scripts/vault_review.py queue [--limit N] [--jurisdiction AL]
                                                       records awaiting review (Alabama, then source-checked)
  scripts/vault_review.py verify BENEFIT_ID --handle H --content-hash HASH [--on YYYY-MM-DD]
  scripts/vault_review.py withdraw BENEFIT_ID [--on YYYY-MM-DD]

A review takes effect in the API on its next start (registry.with_reviews).
"""
import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.domains.vault import review  # noqa: E402
from app.infra.db import DatabaseError, connect  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sync-roster")
    q = sub.add_parser("queue")
    q.add_argument("--limit", type=int, default=25)
    q.add_argument("--jurisdiction")
    v = sub.add_parser("verify")
    v.add_argument("benefit_id")
    v.add_argument("--handle", required=True)
    v.add_argument("--content-hash", required=True)
    v.add_argument("--on", type=dt.date.fromisoformat, default=dt.date.today())
    w = sub.add_parser("withdraw")
    w.add_argument("benefit_id")
    w.add_argument("--on", type=dt.date.fromisoformat, default=dt.date.today())
    args = ap.parse_args(argv)

    dsn = os.environ.get("DATABASE_ADMIN_URL")
    if not dsn:
        print("DATABASE_ADMIN_URL is not set (the owner connection)", file=sys.stderr)
        return 2
    try:
        with connect(dsn) as conn:
            if args.cmd == "sync-roster":
                out = review.sync_roster(conn, review.load_roster(), dt.date.today())
            elif args.cmd == "queue":
                out = review.queue(conn, args.limit, args.jurisdiction)
            elif args.cmd == "verify":
                out = review.verify(conn, args.benefit_id, args.handle, args.content_hash, args.on)
            else:
                registry = json.loads((ROOT / "data/reference/benefit_vault_registry.json").read_text())
                status = next((b["record_status"] for b in registry["benefits"] if b["benefit_id"] == args.benefit_id), None)
                if status is None:
                    raise review.ReviewError(f"no record {args.benefit_id} in the registry")
                out = review.withdraw(conn, args.benefit_id, status, args.on)
    except (review.ReviewError, DatabaseError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
