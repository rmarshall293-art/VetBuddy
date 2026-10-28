# VetBuddy Claude Code Project Rules

Read `docs/VETBUDDY_MASTER_SPEC.md` (v6 directive; v5 and canonical integration v2 preserved as subordinate appendices) before making architecture, database, AI-agent, routing or migration changes.

- VetBuddy is a Veteran Operating System; one Master Mission/Master Case; CRM is a contained subsystem.
- Product layout and module names: `docs/PRODUCT_LAYOUT.md`. Case Management is the core; CRM is the relationship layer, never the core. Governance rules win over layout details (`docs/ADR/0006-product-layout.md`).
- Observe code before making claims; report missing source as `SOURCE_NOT_AVAILABLE`.
- Preserve the Base44 prototype; never overwrite/deprecate a feature without mapped tests and rollback.
- GitHub is the code source of truth; PostgreSQL/Supabase is the canonical data store.
- Modular monolith first; shared /api/v1 contracts, RLS/ABAC, consent, audit, transactional events.
- Agent tool calls go through a Trust Kernel; each agent needs manifest, minimal ContextPacket, approved tools and typed result.
- No fabricated benefit, legal source, eligibility, deadline, school participation, official status, or provider integration.
- Deterministic eligibility and policy services are authoritative; AI explains and drafts, cannot self-approve.
- Never use real PII, V4/V5 health data, keys/tokens or sensitive prompt internals in git, logs, output, or public datasets.
- No direct production writes, destructive migrations, filings, data sharing or external messages without approved human workflows.
- Label implementations IMPLEMENTED_TESTED/IMPLEMENTED_UNVERIFIED/PARTIAL/MOCK/PLANNED/DISABLED/BLOCKED (v6 §0); unavailable material is SOURCE_NOT_AVAILABLE.
- No account collection launches before deletion, export and security are implemented (v6 §3, §15). Guest access never requires an account.
- Eligibility outputs use the v6 vocabulary (PRELIMINARY_MATCH … HUMAN_REVIEW_REQUIRED); the Mission Router is never the eligibility engine.
- No final domain, legal operator, pricing or government partnership is invented; keep them as configurable, release-blocking fields.
- User experience: web/PWA-first, accessible, source-transparent, transition-to-thrive lifecycle.
- No sales/pricing/acquisition/investor work.
- Implement the next bounded vertical slice, test it, update docs/gap matrix, and report commands/results.
- Prefer existing working Vite UI; adopt Next.js only after an ADR and deliberate migration.
- Keep CLAUDE.md short. The full prompt and verified inventories live in `docs/VETBUDDY_MASTER_SPEC.md`.
