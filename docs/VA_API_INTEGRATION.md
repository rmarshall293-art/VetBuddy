# VA API Integration

How VetBuddy integrates with VA systems — mock mode (default) and path to live Lighthouse API.

> **VetBuddy does not have live VA integration in the default configuration.** All VA API calls return mock/fixture data unless explicitly configured with approved Lighthouse credentials.

## Overview

VetBuddy's VA integration is designed around the [VA Lighthouse APIs](https://developer.va.gov), which provide OAuth 2.0 authenticated access to veteran health and benefits data in sandbox and production environments.

### Current Status

| Capability | Mock Mode | Live (Lighthouse) |
|------------|-----------|-------------------|
| Veteran authentication via VA | Fixture login | Requires OAuth registration |
| Claims status lookup | Returns demo claim | Requires Benefits Claims API access |
| Intent to File submission | Local DB only | Requires Benefits Intake API |
| Health records (FHIR) | Not implemented | Requires Health API access |
| Facility lookup | Seed data in `facilities` table | VA Facilities API available |

## Mock Mode (Default)

Mock mode is enabled by default:

```env
VA_MOCK_MODE=true
VA_API_BASE_URL=https://sandbox-api.va.gov
```

### How Mock Mode Works

1. When `VA_MOCK_MODE=true`, the FastAPI backend intercepts VA API calls.
2. Instead of making outbound HTTP requests to VA, the service returns predefined fixture data.
3. Responses are logged to `api_integration_logs` with `integration_name='va_lighthouse_mock'`.
4. Claims created in VetBuddy use local `claims.va_claim_id` values prefixed with `MOCK-`.
5. No veteran data is transmitted to VA systems.

### Mock Data Sources

- Demo claim in `seed_data.sql` (claim ID `f0000000-...`)
- `va_forms` table for form catalog
- `facilities` table for facility directory (populate separately)
- `va_rate_tables` and `cola_tables` for compensation rates

### Why Mock Mode

- VA Lighthouse requires a formal application and approval process
- Sandbox access is limited and requires veteran test accounts
- Development and demos should not depend on external VA availability
- Prevents accidental submission of test data to VA systems

## Live Lighthouse Integration

### Step 1: Register at developer.va.gov

1. Go to [https://developer.va.gov](https://developer.va.gov)
2. Create a developer account
3. Request access to required APIs:
   - **Benefits Claims** — claim status and submission
   - **Benefits Intake** — form submission (21-526EZ, etc.)
   - **Veteran Verification** — confirm veteran status
   - **Facilities** — VA facility locator
   - **Health (FHIR)** — if health records needed (separate approval)

### Step 2: OAuth 2.0 Configuration

VA Lighthouse uses OAuth 2.0 with OpenID Connect:

```env
VA_MOCK_MODE=false
VA_CLIENT_ID=your_client_id
VA_CLIENT_SECRET=your_client_secret
VA_REDIRECT_URI=https://yourdomain.com/api/v1/va/lighthouse/callback
VA_API_BASE_URL=https://sandbox-api.va.gov  # sandbox first
```

OAuth flow:

```
Veteran → VetBuddy → VA Login.gov/ID.me → VA Authorization Server
                                                    ↓
                              VetBuddy ← Authorization Code
                                                    ↓
                              VetBuddy → Token Exchange → Access Token
                                                    ↓
                              VetBuddy → VA API (with Bearer token)
```

Veteran OAuth tokens are stored with:

- `users.oauth_provider = 'va_lighthouse'`
- `users.oauth_subject = <VA veteran ID>`

### Step 3: Sandbox Testing

VA provides sandbox test veterans with known credentials. Use these for integration testing — never use real veteran credentials in development.

Sandbox base URL: `https://sandbox-api.va.gov`
Production base URL: `https://api.va.gov`

### Step 4: Production Access

Production API access requires:

1. Completed sandbox integration testing
2. VA review and approval of your application
3. Security assessment (VA may require additional review for Benefits Intake)
4. Updated privacy policy and terms of service
5. Display of VA non-affiliation disclaimer

## API Endpoints (Planned)

| VetBuddy Endpoint | VA Lighthouse API | Status |
|-------------------|-------------------|--------|
| `GET /api/v1/va/claims` | `GET /services/claims/v1/claims` | Mock |
| `POST /api/v1/va/intent-to-file` | Benefits Intake API | Mock |
| `GET /api/v1/va/facilities` | `GET /services/va_facilities/v1/facilities` | Seed data |
| `GET /api/v1/va/rates` | Local `va_rate_tables` | Local DB |
| `POST /api/v1/va/oauth/callback` | OAuth token endpoint | Scaffold |

## Data Mapping

### Claims

| VetBuddy (`claims`) | VA Lighthouse |
|---------------------|---------------|
| `va_claim_id` | VA claim ID |
| `status` | VA claim phase mapping required |
| `combined_rating` | Combined disability rating |
| `filing_date` | Claim submission date |

### Intent to File

| VetBuddy (`intent_to_file_records`) | VA |
|--------------------------------------|-----|
| `confirmation_number` | VA ITF confirmation |
| `expiration_date` | 1 year from filing |
| `va_itf_id` | VA system ID |

## Logging and Compliance

All VA API calls (live or mock) should be logged to `api_integration_logs`:

- Request endpoint and method
- Response status code
- Duration in milliseconds
- Error messages (no PII in logs)
- Associated `user_id`

PII from VA responses must not be written to application logs. Store in appropriate tables only.

## Error Handling

| VA Error | VetBuddy Behavior |
|----------|-------------------|
| 401 Unauthorized | Prompt veteran to re-authenticate via VA OAuth |
| 403 Forbidden | Display "insufficient VA permissions" message |
| 404 Not Found | Return empty result; no claim found |
| 429 Rate Limited | Exponential backoff; queue retry |
| 5xx Server Error | Log error; display graceful degradation message |

## VA Non-Affiliation Disclaimer

VetBuddy must display:

> VetBuddy is an independent platform and is not affiliated with, endorsed by, or connected to the U.S. Department of Veterans Affairs. For official VA services, visit [va.gov](https://www.va.gov).

This is tracked as complete in `legal_readiness_checklist` (`legal_va_disclaimer`).

## What VetBuddy Cannot Do Today

- Submit live disability claims to VA
- Pull real veteran health records
- Replace VA.gov or eBenefits functionality
- Guarantee claim outcomes or processing times

VetBuddy is a **planning and tracking tool** that can optionally sync with VA data when properly authorized — not a replacement for official VA systems.
