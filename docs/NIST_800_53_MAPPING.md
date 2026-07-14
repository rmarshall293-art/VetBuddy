# NIST 800-53 Control Mapping

Mapping of VetBuddy security controls to NIST SP 800-53 Rev. 5 control families.

> **This is a readiness mapping, not a certification.** VetBuddy has not undergone a formal NIST 800-53 assessment or received an Authority to Operate (ATO).

## Legend

| Status | Meaning |
|--------|---------|
| Implemented | Control exists and is operational |
| Partial | Control started but incomplete |
| Planned | Documented intent, not yet built |
| N/A | Not applicable to current scope |

## Access Control (AC)

| Control | Title | Status | VetBuddy Implementation |
|---------|-------|--------|------------------------|
| AC-2 | Account Management | Partial | `users` table, role assignments, soft-delete |
| AC-3 | Access Enforcement | Implemented | FastAPI RBAC + Postgres RLS |
| AC-6 | Least Privilege | Implemented | Role-based permissions per endpoint |
| AC-7 | Unsuccessful Logins | Planned | Rate limiting scaffold; lockout not implemented |
| AC-11 | Device Lock | N/A | Web application |
| AC-12 | Session Termination | Partial | JWT expiry; `sessions.revoked_at` for refresh tokens |
| AC-17 | Remote Access | Partial | HTTPS required; VPN not applicable |

## Audit and Accountability (AU)

| Control | Title | Status | VetBuddy Implementation |
|---------|-------|--------|------------------------|
| AU-2 | Event Logging | Implemented | `audit_logs`, `api_integration_logs` tables |
| AU-3 | Content of Audit Records | Partial | Actor, action, resource, timestamps logged |
| AU-6 | Audit Review | Planned | No automated audit review tooling |
| AU-9 | Protection of Audit Info | Partial | RLS admin-only on `audit_logs` |
| AU-12 | Audit Generation | Partial | Admin actions logged; not all CRUD operations |

## Identification and Authentication (IA)

| Control | Title | Status | VetBuddy Implementation |
|---------|-------|--------|------------------------|
| IA-2 | Identification and Authentication | Implemented | Email/password + JWT |
| IA-2(1) | MFA for Privileged Accounts | Partial | MFA schema ready; enforcement pending |
| IA-5 | Authenticator Management | Partial | bcrypt hashing; password policy pending |
| IA-8 | Identification and Authentication (Non-Org Users) | Partial | OAuth fields present; not wired |

## System and Communications Protection (SC)

| Control | Title | Status | VetBuddy Implementation |
|---------|-------|--------|------------------------|
| SC-8 | Transmission Confidentiality | Partial | TLS required in deployment docs |
| SC-12 | Cryptographic Key Management | Partial | `SECRET_KEY` via env; no HSM |
| SC-13 | Cryptographic Protection | Partial | bcrypt, JWT signing, MFA encryption field |
| SC-28 | Protection of Information at Rest | Partial | Cloud provider disk encryption |

## System and Information Integrity (SI)

| Control | Title | Status | VetBuddy Implementation |
|---------|-------|--------|------------------------|
| SI-2 | Flaw Remediation | Planned | Dependency scanning in CI checklist |
| SI-3 | Malicious Code Protection | N/A | No endpoint agent; cloud provider responsibility |
| SI-4 | System Monitoring | Partial | Structured logging; Sentry optional |
| SI-10 | Information Input Validation | Implemented | Pydantic request validation |

## Configuration Management (CM)

| Control | Title | Status | VetBuddy Implementation |
|---------|-------|--------|------------------------|
| CM-2 | Baseline Configuration | Partial | `canonical_migration.sql` as schema baseline |
| CM-6 | Configuration Settings | Partial | Environment-based config via Pydantic Settings |
| CM-8 | System Component Inventory | Partial | README and docs inventory |

## Contingency Planning (CP)

| Control | Title | Status | VetBuddy Implementation |
|---------|-------|--------|------------------------|
| CP-9 | System Backup | Planned | Cloud provider backup configuration required |
| CP-10 | System Recovery | Planned | No documented DR runbook |

## Risk Assessment (RA)

| Control | Title | Status | VetBuddy Implementation |
|---------|-------|--------|------------------------|
| RA-5 | Vulnerability Monitoring | Planned | `sec_dependency_scan` checklist item |
| RA-3 | Risk Assessment | Planned | Security and legal checklists as starting point |

## Planning (PL)

| Control | Title | Status | VetBuddy Implementation |
|---------|-------|--------|------------------------|
| PL-2 | System Security Plan | Partial | This document + SECURITY.md |
| PL-4 | Rules of Behavior | Planned | Terms of service checklist item |

## Gap Summary

### Strengths

- Role-based access control at application and database layers
- Audit log schema with immutable records
- Password hashing with bcrypt
- Soft-delete for sensitive entities
- Security checklist tracking in database

### Gaps (Priority Order)

1. MFA enforcement for privileged accounts
2. Automated vulnerability scanning in CI
3. Formal incident response runbook
4. Backup and disaster recovery documentation
5. Complete audit coverage for all data mutations
6. Password policy enforcement
7. Key management beyond environment variables
8. Penetration testing

## Path to Formal Assessment

To pursue a formal NIST 800-53 assessment (e.g., for federal agency deployment):

1. Complete gap items above
2. Engage a Third Party Assessment Organization (3PAO) for FedRAMP or agency ATO
3. Produce System Security Plan (SSP)
4. Conduct Security Assessment Report (SAR)
5. Obtain Authorizing Official (AO) sign-off

**Current status: Pre-assessment readiness documentation only.**
