"""Benefit Vault domain (migration 0014).

The Benefit Vault is VetBuddy's benefits-and-deals finder: state and federal
benefits, scholarships, park passes, hunting and fishing licenses, plates,
tax relief and family programs for active duty, National Guard, Reserve,
veterans and their families.

Layout, by system plane:

- Plane 4, source intelligence: ``registry`` (the canonical catalog),
  ``rules`` (the rule language compiler), ``discovery`` (planner, watcher,
  legacy importer).
- Plane 2, work OS: ``matcher`` (the deterministic kernel), ``search`` and
  ``household`` (facts for a spouse or child derived from the sponsor's).
- Plane 3, secure context fabric: ``governance`` (manifests, grants, context
  packets, the pull broker, the hash-chained pull ledger, the egress guard).
- Plane 5, AI workforce: ``agent`` (the Benefit Vault agent, the only agent
  allowed to pull facts from other agents, and only under a user grant).
- Storage: ``vault_store`` (PostgreSQL, migration 0014: Mode B account
  grants, the pull ledger and saved benefits, all under row-level security).
- API: ``api`` (Starlette routes under ``/api/v1/vault``).

The governing sentence of the platform holds here: agents orchestrate, gather
and explain; they never decide. Every outcome comes from the deterministic
kernel in ``matcher`` and uses the v6 outcome vocabulary.
"""

ENGINE_NAME = "vetbuddy.vault.matcher"
ENGINE_VERSION = "1.0.0"
REGISTRY_NAME = "vetbuddy.benefit_vault_registry"
VAULT_AGENT_ID = "benefit_vault_agent"
