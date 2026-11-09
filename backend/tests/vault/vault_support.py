"""Constants shared by the vault tests (imported as a plain module; the runner puts this folder on sys.path)."""
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS = tuple(sorted((ROOT / "database" / "migrations").glob("*.sql")))
MIGRATION = ROOT / "database" / "migrations" / "0014_benefit_vault.sql"
SEED = ROOT / "database" / "seeds" / "0014_benefit_vault_seed.sql"
SEEDS = (ROOT / "database" / "seeds" / "0011_reference.sql", SEED)

NOW = datetime(2026, 10, 27, 15, 0, 0, 123456, tzinfo=timezone.utc)
AS_OF = "2026-10-27"
TENANT_A = "0f6c7e1e-1111-4222-8333-444455556666"
TENANT_B = "7a1d2c3b-aaaa-4bbb-8ccc-ddddeeeeffff"
