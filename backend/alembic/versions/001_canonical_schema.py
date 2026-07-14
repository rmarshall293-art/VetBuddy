"""Initial canonical schema migration.

Production deployments may alternatively apply SQL files in order:
  1. database/schema.sql
  2. database/indexes.sql
  3. database/views.sql
  4. database/rls_policies.sql  (or backend/app/db/rls.sql)
  5. database/seed_data.sql     (optional, dev/demo only)

This Alembic revision creates all ORM-defined tables for environments that
prefer programmatic migrations over raw SQL.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_canonical_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  """Create all tables from SQLAlchemy metadata."""
  from app.db.database import Base
  from app.db import models  # noqa: F401

  bind = op.get_bind()
  Base.metadata.create_all(bind=bind)


def downgrade() -> None:
  """Drop all ORM tables (destructive — dev/test only)."""
  from app.db.database import Base
  from app.db import models  # noqa: F401

  bind = op.get_bind()
  Base.metadata.drop_all(bind=bind)
