"""Single loader for the unverified-jurisdiction disclaimer (config is the
one source; no route restates the text)."""
from pathlib import Path

import yaml

_PATH = Path(__file__).parents[3] / "config" / "jurisdiction_status.yaml"
UNVERIFIED_DISCLAIMER: str = " ".join(yaml.safe_load(_PATH.read_text())["unverified_disclaimer"].split())


def labelled(row: dict) -> dict:
    out = {"code": row["code"], "name": row["name"], "kind": row["kind"],
           "verification_status": row["verification_status"]}
    if row["verification_status"] != "verified":
        out["disclaimer"] = UNVERIFIED_DISCLAIMER
    return out
