# Account deletion runbook (master prompt v6 §3)

## What exists today

| Piece | Where | Notes |
|---|---|---|
| In-app request | Web shell → Privacy → Delete account | One confirmation step (typed phrase); optional export first; no obstruction |
| API | `POST /api/v1/me/delete` `{"confirm": "DELETE MY ACCOUNT"}` | Authenticated; any other body → 422 |
| Export | `GET /api/v1/me/export` | Every row of every tenant table for the account; works after consent withdrawal |
| Purge | `vb_delete_account(user_id)` (migration 0013) | One transaction; owned by `vetbuddy_purger` (NOLOGIN, NOBYPASSRLS), so forced RLS scopes every delete to the caller's tenant |
| Receipt | `privacy_deletion_receipt`; public `GET /api/v1/privacy/deletions/{receipt_id}` | State history, per-table counts, processors, exceptions; dates only; no user, tenant, email or content |
| Session revocation | `protected` wrapper | Every protected request re-checks the account exists; deleted → 401 `SESSION_INVALID` |

## How the purge works

1. Check: caller's tenant context is set; the user exists in that tenant; the
   tenant is `individual` with exactly one user. Shared tenants are refused
   (`SHARED_ACCOUNT_NOT_SUPPORTED`) instead of over-deleting.
2. Record states REQUESTED → VERIFIED → ACCESS_REVOKED → PURGING.
3. Delete from every public table with a `tenant_id`, repeating passes until
   foreign keys allow every row to go. A pass that removes nothing while rows
   remain aborts the whole transaction, so nothing is left half-deleted.
4. `audit_event` is append-only; its trigger allows deletes only while
   `vetbuddy.purge_tenant` equals that tenant, a setting only the function
   sets. The app role has no DELETE grant anywhere.
5. PROCESSOR_PENDING → COMPLETE. No processors are registered in this build.

Because the purge is one transaction, a failure rolls everything back and the
API returns a retryable error; `FAILED_RETRYABLE` becomes a stored state once
external processors exist (their calls happen after the local commit).

## Adding a new tenant table

Grant `SELECT, DELETE` on it to `vetbuddy_purger` in the same migration.
`test_purger_role_cannot_bypass_rls_and_covers_every_tenant_table` fails
otherwise, and without the grant deletion fails closed.

## Before real accounts launch (release blockers)

- **Identity:** proportional reauthentication (step-up) before deletion; a
  public deletion request route with identity verification for people who
  uninstalled the app (G17).
- **Backups:** approved expiry schedule, restricted restore, and a
  deletion-replay step that re-applies receipts before a restored database
  serves traffic. Never promise immediate removal from every backup.
- **Processors:** each provider (email, model, storage, analytics) is listed
  on the receipt with acknowledgement, failure and retry.
- **Legal holds and organization records:** inventory, basis, deadline;
  retained material restricted; the receipt states each exception plainly.
- **Store accounts:** subscription cancellation, if billing is ever enabled,
  stays independent of deletion; Sign in with Apple token revocation when used.
