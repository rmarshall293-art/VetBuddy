# Architecture (as built)

Modular monolith. The governing sentence: **agents orchestrate, gather and explain; they never decide.** Today no agent exists; every answer comes from deterministic kernels.

```mermaid
flowchart LR
  subgraph Browser
    G[Guest views<br/>kernel.js + kernel_data.js] -->|no network| G
    P[Saved plan view<br/>plan.js] -->|Bearer dev token| API
  end
  subgraph API[FastAPI /api/v1]
    PUB[public.py<br/>router, ratings, crisis, jurisdictions] --> K[kernel/<br/>router.py ratings.py]
    PRIV[private.py<br/>users, consents, missions, cases, tasks] --> AUTH[auth.verify_token<br/>swap point G17]
    PRIV --> SVC[services/work.py]
    SVC --> K
  end
  SVC -->|one transaction, app.tenant_id/app.user_id LOCAL| DB[(PostgreSQL vb<br/>FORCE RLS)]
  DB --> AUD[audit_events<br/>hash chain, append-only]
  DB --> OUT[outbox<br/>no dispatcher yet]
  PY[scripts/build_web.py] -->|generates| G
```

## Request: save a Mission Brief (Mode B)

```mermaid
sequenceDiagram
  participant W as Web (plan.js)
  participant A as API
  participant D as PostgreSQL (as vetbuddy_app)
  W->>A: POST /api/v1/missions (declared facts only)
  A->>A: verify token -> Principal (subject from token)
  A->>D: resolve_principal(tenant, subject)
  A->>D: BEGIN; set_config(app.tenant_id, app.user_id, LOCAL)
  A->>D: has_consent('plan_storage')?  (else 409, nothing stored)
  A->>A: kernel.route(facts, today) — deterministic
  A->>D: INSERT mission, case, lanes, tasks (RLS WITH CHECK incl. consent)
  A->>D: INSERT audit (chained by trigger), outbox MISSION_CREATED, CASE_CREATED
  A->>D: COMMIT
  A-->>W: Mission Brief (+ disclosure, disclaimer)
```

## Data ownership

| Data | Owner | Who may write |
|---|---|---|
| Identity mapping (`users`) | Trust & Identity | `resolve_principal` (definer) only |
| Consent | Privacy & Consent Guardian (SQL) | The user, via API; allowlist CHECK |
| Mission / case / lanes / tasks | Work OS | Owner, with live consent |
| Audit | Operations | Append via API; chain by trigger; nobody updates |
| Router rules & wording | `kernel/vocab.py` | Code review only |

## Privacy modes

- **A Guest:** browser-only, or `POST /mission-router/evaluate` (stateless). Proven to write nothing.
- **B Personal:** saved plans with `plan_storage` consent.
- **C Managed case:** refused by `CHECK (privacy_mode = 'B')`.
