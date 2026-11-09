# Current State Audit — 2026-10-20 (slice 01 session)

## Verified current baseline

| Item | Observed | How |
|---|---|---|
| GitHub `rmarshall293-art/VetBuddy` | **SOURCE_NOT_AVAILABLE** this session. GitHub was not linked to the build session, so the repo could not be re-scanned. The last recorded observation (master spec §1A) is a public repo with CI/config only. | `add_repo` returned "link your GitHub account" |
| Base44 export | **SOURCE_NOT_AVAILABLE** | Not supplied |
| Skeleton v1 (`vetbuddy-skeleton.zip`) | 8 SQL migrations, 5 FastAPI router stubs (all `NotImplementedError`), crisis-floor config + loader, agent registry JSON, docs | Unzipped; committed unmodified as baseline `04e0431` |
| Migrations 0001–0008 | **Apply cleanly** to PostgreSQL 16.15 (46 tables) | `psql -v ON_ERROR_STOP=1 -f` each file, exit 0 |
| Package registries | pip/npm blocked (proxy 403) | `pip install fastapi`, `npm view vite` |

## Defects found by running the skeleton (all fixed in `0009`)

| # | Finding | Evidence | Fix |
|---|---|---|---|
| F1 | `household` has `tenant_id` but RLS is **off**, so cross-tenant reads are possible | `pg_class.relrowsecurity = false` | RLS enabled + forced |
| F2 | `tenant` table has RLS off | same | enabled + forced |
| F3 | **No table uses FORCE RLS**, so a backend connecting as the table owner bypasses every policy | `count(relforcerowsecurity)=0` | FORCE on every tenant table; API connects as non-owner `vb_app` |
| F4 | Policies call `current_setting('vetbuddy.tenant_id')` without `missing_ok`, so an unset context throws an error instead of returning no rows | `ERROR: unrecognized configuration parameter` | `vb_current_tenant()` returns NULL, which matches no row |
| F5 | No explicit `WITH CHECK` | policy definitions | uniform `USING` + `WITH CHECK` |
| F6 | 4 agent manifests seeded `PRODUCTION` with empty data classes and tools | `SELECT … WHERE status='PRODUCTION'` | downgraded to `DRAFT` |
| F7 | `app_user.privacy_mode='C'` was reachable by a plain update | — | `managed_requires_flag` CHECK |
| F8 | Any consent purpose string was storable | — | `consent_purpose` allowlist FK |

0009 ends with a guard that **fails the migration** if any tenant table lacks enabled + forced RLS, or if any RLS table has no policy.

## Security exposure notes

- The repo was last observed **public**. `docs/sources/` (business plan, funding request, full prompts) is gitignored until you decide what to publish.
- No secrets exist in this tree. `.env.example` holds placeholders only.
- The skeleton's `render.yaml` with the legacy `SUPABASE_SERVICE_ROLE_KEY` name is in the GitHub repo, not this tree, so it was not inspected (SOURCE_NOT_AVAILABLE).
