"""Evidence service module (re-exports claims evidence helpers)."""

from app.services.claims_service import add_evidence, list_evidence

__all__ = ["add_evidence", "list_evidence"]
