# Legal and Contracting Readiness

Checklist and documentation for VetBuddy's legal posture and government contracting readiness.

> **This is a readiness checklist, not legal advice.** Consult qualified attorneys and contracting specialists before pursuing government contracts.

## Overview

VetBuddy aims to serve veterans directly (B2C subscription) and partner with Veteran Service Organizations and state departments (B2B/B2G). Government contracting requires specific registrations, certifications, and compliance documentation.

Progress is tracked in the `legal_readiness_checklist` database table.

## Business Structure Requirements

### Service-Disabled Veteran-Owned Small Business (SDVOSB)

| Item | Status | Notes |
|------|--------|-------|
| Business entity formed | Required | LLC, Corp, or other legal entity |
| 51%+ owned by service-disabled veteran(s) | Required | Per SBA regulations |
| Day-to-day control by service-disabled veteran | Required | Management and decision-making |
| SBA VetCert certification | Pending | Apply at [veterans.sba.gov](https://veterans.sba.gov) |
| VA CVE verification (legacy) | N/A | Replaced by SBA VetCert program |

**SDVOSB certification** provides set-aside eligibility for federal contracts under NAICS codes applicable to software/IT services.

### NAICS Codes (Candidate)

| Code | Description |
|------|-------------|
| 541511 | Custom Computer Programming Services |
| 541512 | Computer Systems Design Services |
| 541519 | Other Computer Related Services |
| 611430 | Professional and Management Development Training |

Select primary and secondary NAICS codes during SAM.gov registration.

## SAM.gov Registration

The System for Award Management (SAM.gov) is required for any federal contract, grant, or cooperative agreement.

### Registration Checklist

| Step | Status | Details |
|------|--------|---------|
| Create SAM.gov account | Pending | [sam.gov](https://sam.gov) |
| Obtain UEI | Pending | Unique Entity Identifier (replaces DUNS) |
| Obtain CAGE Code | Pending | Assigned during SAM registration |
| Complete entity registration | Pending | Business info, banking (EFT), reps & certs |
| NAICS codes selected | Pending | See above |
| PSC codes selected | Pending | Product Service Codes for IT services |
| Annual renewal | N/A | SAM registration must be renewed annually |

### Key Identifiers

Stored in `organizations` table for demo:

| Field | Column | Example |
|-------|--------|---------|
| UEI | `organizations.uei` | 12-character alphanumeric |
| CAGE Code | `organizations.cage_code` | 5-character code |
| EIN | `organizations.ein` | Federal tax ID |

**Do not use demo UEI/CAGE values for real registrations.**

## Contracting Vehicles

### Potential Paths to Government Revenue

| Vehicle | Description | VetBuddy Fit |
|---------|-------------|--------------|
| GSA Schedule (IT 70) | Pre-negotiated government pricing | Long-term goal; requires established track record |
| SBIR/STTR | Small business innovation research | Potential for R&D phase |
| Agency BPA/IDIQ | Blanket purchase agreements | Requires agency relationship |
| State contracts | State-level procurement | Alabama DVA, state IT contracts |
| Direct B2B | VSO licensing agreements | Near-term revenue path |

### Recommended Near-Term Path

1. **B2C launch** — Stripe subscription ($5.99/month) for direct veteran users
2. **B2B pilots** — Partner with Alabama VSO chapters for pilot deployments
3. **SAM.gov registration** — Establish federal contracting eligibility
4. **SDVOSB certification** — Unlock set-aside opportunities
5. **State procurement** — Pursue state-level contracts (e.g., Alabama VA department)

## Legal Documents Required

| Document | Status | Checklist Key |
|----------|--------|---------------|
| Privacy Policy | Pending | `legal_privacy_policy` |
| Terms of Service | Pending | `legal_terms_of_service` |
| VA Non-Affiliation Disclaimer | Complete | `legal_va_disclaimer` |
| Data Processing Agreement (B2B) | Pending | `legal_data_processing` |
| Stripe Terms Compliance | Pending | `legal_stripe_tos` |
| Acceptable Use Policy | Not started | — |
| Cookie Policy | Not started | — |

### Privacy Policy Requirements

Must address:

- Categories of veteran PII collected (name, service history, claim data)
- Purpose of data collection
- Third-party sharing (Stripe, VA Lighthouse if enabled)
- Data retention and deletion (soft-delete policy)
- User rights (access, correction, deletion)
- Contact information for privacy inquiries
- State privacy law compliance (CCPA, etc.)

### Terms of Service Requirements

Must address:

- Subscription billing terms ($5.99/month, cancellation, refunds)
- Disclaimer that VetBuddy is not VA-affiliated
- Limitation of liability (not providing legal/medical advice)
- Account termination conditions
- Dispute resolution

## Compliance and Accessibility

| Requirement | Status | Notes |
|-------------|--------|-------|
| Section 508 / WCAG 2.1 AA | Pending | `legal_accessibility` checklist item |
| State breach notification | Pending | Incident response plan needed |
| Cyber liability insurance | Pending | `legal_insurance` checklist item |
| E&O insurance | Pending | Errors and omissions for software |

## Intellectual Property

| Item | Recommendation |
|------|----------------|
| Trademark "VetBuddy" | Conduct USPTO search; file if clear |
| Open source dependencies | Maintain license inventory (MIT, Apache, etc.) |
| VA form PDFs | VA forms are public domain; VetBuddy guides are proprietary |
| Benefits data | Verify licensing for third-party data sources |

## Insurance

| Type | Purpose | Status |
|------|---------|--------|
| Cyber liability | Data breach coverage | Pending |
| E&O (Professional liability) | Software errors affecting veterans | Pending |
| General liability | Standard business coverage | Pending |
| Workers compensation | If employees | N/A (solo/contractor) |

Many government contracts require minimum insurance coverage ($1M–$2M general liability, $1M cyber).

## Incident Response

Tracked as `legal_incident_response` in checklist. Required elements:

1. Incident classification criteria
2. Notification timeline (72 hours for many state breach laws)
3. VA notification if veteran data from Lighthouse is compromised
4. Customer notification procedures
5. Post-incident review process

## Government Contract Clauses

When pursuing federal contracts, expect to address:

- **FAR 52.212-4** — Commercial item contract terms
- **FAR 52.204-21** — Basic safeguarding of CUI (if handling controlled data)
- **DFARS 252.204-7012** — NIST 800-171 if handling DoD CUI
- **FAR 52.219-14** — Limitations on subcontracting (SDVOSB)
- **FAR 52.222-50** — Combating trafficking in persons

VetBuddy does not currently handle Controlled Unclassified Information (CUI) or DoD data.

## Database Checklist Queries

View legal readiness status:

```sql
SELECT item_key, title, status, priority
FROM legal_readiness_checklist
ORDER BY
    CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
    category;
```

Mark item complete:

```sql
UPDATE legal_readiness_checklist
SET status = 'complete',
    completed_at = NOW(),
    completed_by = '<admin-user-uuid>'
WHERE item_key = 'legal_sam_registration';
```

## Timeline Recommendation

| Phase | Timeframe | Actions |
|-------|-----------|---------|
| 1 — Foundation | Month 1–2 | Privacy policy, ToS, VA disclaimer, Stripe compliance |
| 2 — Registration | Month 2–4 | SAM.gov, UEI, CAGE, SDVOSB application |
| 3 — Insurance | Month 3–4 | Cyber liability, E&O policies |
| 4 — Accessibility | Month 4–6 | WCAG audit and remediation |
| 5 — Contracting | Month 6+ | Pursue pilot contracts, GSA assessment |

## What VetBuddy Is Not

- **Not a law firm** — does not provide legal advice on claims
- **Not a VSO** — not accredited by VA to represent veterans
- **Not a medical provider** — does not provide medical advice
- **Not VA-affiliated** — independent commercial platform

Veterans should be directed to accredited VSOs and VA.gov for official claim representation and submission.

## Resources

- [SAM.gov](https://sam.gov) — Entity registration
- [SBA VetCert](https://veterans.sba.gov) — SDVOSB certification
- [VA Office of Small & Disadvantaged Business Utilization](https://www.va.gov/osdbu/)
- [GSA Schedule IT](https://www.gsa.gov/buying-selling/products-services/information-technology)
- [Section 508 Compliance](https://www.section508.gov/)
