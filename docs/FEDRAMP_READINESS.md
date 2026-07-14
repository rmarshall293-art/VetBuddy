# FedRAMP Readiness

## Status: NOT FedRAMP Certified

**VetBuddy is not FedRAMP authorized.** This document is an honest gap analysis and readiness checklist — not a claim of compliance or certification.

FedRAMP (Federal Risk and Authorization Management Program) requires a rigorous third-party assessment, continuous monitoring, and an Authorizing Official sign-off. VetBuddy has not begun this process.

## What FedRAMP Requires

FedRAMP authorization means a cloud service offering has been assessed against NIST SP 800-53 controls at Low, Moderate, or High baseline, and has received a Provisional Authority to Operate (P-ATO) from the FedRAMP JAB or an agency AO.

## VetBuddy FedRAMP Readiness Checklist

| # | Requirement | Status | Notes |
|---|-------------|--------|-------|
| 1 | FedRAMP boundary definition | Not started | Define system boundary, data flows, interconnections |
| 2 | NIST 800-53 SSP | Not started | See [NIST_800_53_MAPPING.md](./NIST_800_53_MAPPING.md) |
| 3 | 3PAO security assessment | Not started | Requires budget ($200K–$500K+ typical) |
| 4 | Continuous monitoring program | Not started | Monthly scanning, annual assessment |
| 5 | FIPS 140-2 validated cryptography | Not verified | Cloud provider may provide; not validated at app layer |
| 6 | US-only data residency | Not configured | Requires explicit cloud region selection |
| 7 | Incident response plan | Partial | Checklist item exists; no formal IRP |
| 8 | POA&M process | Not started | Plan of Action and Milestones for findings |
| 9 | Configuration management | Partial | Schema versioning via migration files |
| 10 | Personnel security | Not started | Background checks for admin access |
| 11 | Contingency planning | Not started | DR/backup runbooks needed |
| 12 | Supply chain risk management | Not started | Dependency provenance tracking |
| 13 | Privacy impact assessment | Not started | PIA required for veteran PII |
| 14 | FedRAMP package submission | Not started | |

## Why VetBuddy Is Not FedRAMP Ready Today

1. **No formal security assessment** has been conducted.
2. **MFA is not enforced** for privileged accounts.
3. **No continuous monitoring** program or SIEM integration.
4. **No documented disaster recovery** plan or tested backups.
5. **No FIPS-validated cryptography** at the application layer.
6. **No incident response plan** with defined notification timelines.
7. **No POA&M** for tracking and remediating findings.
8. **Mock VA integration** — live federal system interconnection not assessed.
9. **No penetration test** by a qualified assessor.
10. **No FedRAMP boundary diagram** or data flow documentation.

## What VetBuddy Has Done (Foundation)

These items provide a starting point but are insufficient for FedRAMP:

- PostgreSQL RLS policies for data isolation
- RBAC with admin/veteran/RO role separation
- Audit log table schema
- Security and legal readiness checklists in database
- NIST 800-53 control mapping (readiness document)
- Encryption-at-rest via cloud Postgres providers
- bcrypt password hashing
- Environment-based secrets (no hardcoded keys)

## If Pursuing FedRAMP in the Future

### Recommended Path

1. **Select baseline:** Likely FedRAMP Moderate for veteran PII
2. **Choose impact level cloud:** AWS GovCloud, Azure Government, or GCP Assured Workloads
3. **Engage 3PAO:** Select from FedRAMP marketplace
4. **Build SSP:** Document all 800-53 controls with implementation details
5. **Remediate gaps:** Address findings from readiness assessment
6. **Submit package:** JAB or agency sponsorship required
7. **Continuous monitoring:** Ongoing ConMon per FedRAMP requirements

### Estimated Timeline and Cost

| Phase | Duration | Estimated Cost |
|-------|----------|----------------|
| Readiness assessment | 2–3 months | $30K–$75K |
| Remediation | 3–6 months | $50K–$150K |
| 3PAO assessment | 3–6 months | $200K–$500K |
| Continuous monitoring (annual) | Ongoing | $100K–$300K/year |

*Estimates vary widely based on scope, cloud provider, and assessor.*

## Alternative: Agency ATO

Federal agencies can grant their own Authority to Operate without full FedRAMP authorization. This may be more appropriate for a pilot deployment with a single agency sponsor. Requirements are similar but scoped to the agency's risk tolerance.

## Disclaimer

This document does not constitute legal advice. Consult a FedRAMP consultant and your agency sponsor before pursuing authorization.

**VetBuddy is a commercial veteran support tool. It is not a federal system and is not FedRAMP authorized.**
