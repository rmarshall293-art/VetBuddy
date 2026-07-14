export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserProfile {
  id: string;
  display_name?: string | null;
  preferred_jurisdiction?: string | null;
  service_branch?: string | null;
  service_era?: string | null;
  phone?: string | null;
  city?: string | null;
  state?: string | null;
  zip_code?: string | null;
  bio?: string | null;
}

export interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  mfa_enabled: boolean;
  roles: string[];
  profile?: UserProfile | null;
  created_at?: string | null;
}

export interface ClaimCondition {
  id?: string;
  condition_name: string;
  current_diagnosis?: string | null;
  in_service_event?: string | null;
  nexus_evidence?: string | null;
  current_symptoms?: string | null;
  treatment_history?: string | null;
  diagnostic_code?: string | null;
  claimed_rating?: number | null;
}

export interface Evidence {
  id: string;
  claim_id: string;
  evidence_type: string;
  title: string;
  description?: string | null;
  status: string;
  checklist_item?: string | null;
  strength_weight?: string | null;
}

export interface Claim {
  id: string;
  title: string;
  status: string;
  claim_type: string;
  intent_to_file_date?: string | null;
  evidence_strength_score?: string | null;
  missing_evidence_warnings?: unknown;
  appeal_path?: string | null;
  notes?: string | null;
  disclaimer_acknowledged: boolean;
  conditions: ClaimCondition[];
  evidence: Evidence[];
  created_at?: string | null;
}

export interface Jurisdiction {
  id: string;
  code: string;
  name: string;
  jurisdiction_type: string;
  veteran_population?: number | null;
  cost_of_living_index?: string | number | null;
  housing_affordability_index?: string | number | null;
  unemployment_rate?: string | number | null;
  military_retirement_tax_rule?: string | null;
  va_disability_tax_rule?: string | null;
  property_tax_benefits_summary?: string | null;
  education_benefits_summary?: string | null;
  veterans_home_summary?: string | null;
  healthcare_access_score?: string | number | null;
  gi_bill_usage_metric?: string | number | null;
  state_veterans_agency_name?: string | null;
  state_veterans_agency_url?: string | null;
  last_reviewed?: string | null;
  confidence_score?: string | number | null;
  citations?: string[] | null;
  notes?: string | null;
  data_status: string;
  ranking_score?: string | number | null;
}

export interface ComparisonResult {
  from_jurisdiction: Jurisdiction;
  to_jurisdiction: Jurisdiction;
  metrics: Record<string, unknown>;
  placeholder_warning: boolean;
  alabama_quick_compare?: Record<string, unknown> | null;
  citations?: string[];
  confidence?: Record<string, string | number>;
}

export interface Benefit {
  id: string;
  name: string;
  category: string;
  summary?: string | null;
  eligibility?: string | null;
  source?: string | null;
  url?: string | null;
  jurisdiction_code?: string | null;
  data_status: string;
}

export interface VaForm {
  id: string;
  form_number: string;
  title: string;
  description?: string | null;
  url?: string | null;
  category?: string | null;
  guidance?: string | null;
}

export interface ChecklistItem {
  id: string;
  code: string;
  title: string;
  description?: string | null;
  status: string;
  notes?: string | null;
  value?: string | null;
}

export interface LoadTestResult {
  id: string;
  run_name: string;
  tool: string;
  concurrent_users?: number | null;
  total_requests?: number | null;
  failure_rate?: string | number | null;
  p95_latency_ms?: string | number | null;
  notes?: string | null;
  report?: Record<string, unknown> | null;
}

export interface SubscriptionStatus {
  tier: string;
  status: string;
  current_period_end?: string | null;
  price_cents: number;
}

export interface CheckoutSession {
  checkout_url: string;
  session_id: string;
  mock: boolean;
}

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
  database: string;
  va_mode: string;
  stripe_mode: string;
}

export interface IntentToFileChecklist {
  title?: string;
  steps: Array<{
    id?: number;
    step?: number;
    title: string;
    detail?: string;
    description?: string;
    form?: string;
  }>;
  disclaimer: string;
  reminders?: string[];
}

export interface AlabamaBenefit {
  name: string;
  category?: string;
  summary?: string;
  eligibility?: string;
  url?: string;
}

export interface CountyOffice {
  id?: string;
  name: string;
  facility_type?: string;
  city?: string;
  address?: string;
  phone?: string;
  url?: string;
  data_status?: string;
}

export interface ApiError {
  detail: string | { msg: string }[];
}

export const COMPARISON_METRICS = [
  { key: 'veteran_population', label: 'Veteran Population' },
  { key: 'cost_of_living_index', label: 'Cost of Living Index' },
  { key: 'housing_affordability_index', label: 'Housing Affordability' },
  { key: 'unemployment_rate', label: 'Unemployment Rate' },
  { key: 'healthcare_access_score', label: 'Healthcare Access' },
  { key: 'gi_bill_usage_metric', label: 'GI Bill Usage' },
  { key: 'military_retirement_tax_rule', label: 'Military Retirement Tax' },
  { key: 'va_disability_tax_rule', label: 'VA Disability Tax' },
  { key: 'property_tax_benefits_summary', label: 'Property Tax Benefits' },
  { key: 'education_benefits_summary', label: 'Education Benefits' },
  { key: 'veterans_home_summary', label: 'Veterans Homes' },
  { key: 'ranking_score', label: 'Ranking Score' },
] as const;
