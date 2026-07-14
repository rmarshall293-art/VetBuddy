import { getAccessToken, getRefreshToken, setTokens, clearTokens } from './auth';
import type {
  TokenResponse,
  User,
  Claim,
  Jurisdiction,
  ComparisonResult,
  Benefit,
  VaForm,
  ChecklistItem,
  LoadTestResult,
  SubscriptionStatus,
  CheckoutSession,
  HealthResponse,
  IntentToFileChecklist,
} from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export class ApiClientError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: unknown,
  ) {
    super(message);
    this.name = 'ApiClientError';
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  auth = false,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (auth) {
    const token = getAccessToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let detail: unknown;
    try {
      detail = await res.json();
    } catch {
      detail = res.statusText;
    }
    const message =
      typeof detail === 'object' && detail !== null && 'detail' in detail
        ? String((detail as { detail: unknown }).detail)
        : `Request failed (${res.status})`;
    throw new ApiClientError(message, res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// Auth
export async function register(data: {
  email: string;
  password: string;
  display_name?: string;
  preferred_jurisdiction?: string;
}): Promise<TokenResponse> {
  return request<TokenResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ ...data, role: 'veteran' }),
  });
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  return request<TokenResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function logout(): Promise<void> {
  const refresh = getRefreshToken();
  if (refresh) {
    try {
      await request('/auth/logout', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: refresh }),
      });
    } catch {
      // ignore logout errors
    }
  }
  clearTokens();
}

export { setTokens, clearTokens, getAccessToken, isAuthenticated } from './auth';

// Users
export async function getMe(): Promise<User> {
  return request<User>('/users/me', {}, true);
}

// Claims
export async function listClaims(): Promise<Claim[]> {
  return request<Claim[]>('/claims', {}, true);
}

export async function getClaim(id: string): Promise<Claim> {
  return request<Claim>(`/claims/${id}`, {}, true);
}

export async function createClaim(data: {
  title: string;
  claim_type?: string;
  disclaimer_acknowledged?: boolean;
}): Promise<Claim> {
  return request<Claim>(
    '/claims',
    { method: 'POST', body: JSON.stringify(data) },
    true,
  );
}

// States
export async function listStates(): Promise<Jurisdiction[]> {
  return request<Jurisdiction[]>('/states');
}

export async function compareStates(
  from: string,
  to: string,
): Promise<ComparisonResult> {
  return request<ComparisonResult>(`/states/compare?from=${from}&to=${to}`);
}

export async function customCompare(data: {
  from_code: string;
  to_code: string;
  metrics?: string[];
}): Promise<ComparisonResult> {
  return request<ComparisonResult>('/states/compare/custom', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// Alabama
export async function getAlabamaBenefits(): Promise<{
  jurisdiction: string;
  placeholder_warning: boolean;
  benefits: unknown[];
  disclaimer: string;
}> {
  return request('/alabama/benefits');
}

export async function getAlabamaTraining(): Promise<Record<string, unknown>> {
  return request('/alabama/resource-officer-training');
}

export async function getAlabamaOffices(): Promise<{
  jurisdiction: string;
  offices: unknown[];
  data_status: string;
}> {
  return request('/alabama/county-offices');
}

export async function getAlabamaRanking(): Promise<Record<string, unknown>> {
  return request('/alabama/ranking');
}

// Benefits
export async function searchBenefits(q: string): Promise<Benefit[]> {
  return request<Benefit[]>(`/benefits/search?q=${encodeURIComponent(q)}`);
}

export async function listBenefits(params?: {
  jurisdiction?: string;
  category?: string;
}): Promise<Benefit[]> {
  const search = new URLSearchParams();
  if (params?.jurisdiction) search.set('jurisdiction', params.jurisdiction);
  if (params?.category) search.set('category', params.category);
  const qs = search.toString();
  return request<Benefit[]>(`/benefits${qs ? `?${qs}` : ''}`);
}

// Forms
export async function listForms(): Promise<VaForm[]> {
  return request<VaForm[]>('/forms');
}

export async function getIntentToFileChecklist(): Promise<IntentToFileChecklist> {
  return request<IntentToFileChecklist>('/intent-to-file/checklist');
}

// Payments
export async function createCheckoutSession(): Promise<CheckoutSession> {
  return request<CheckoutSession>(
    '/payments/create-checkout-session',
    { method: 'POST' },
    true,
  );
}

export async function getSubscriptionStatus(): Promise<SubscriptionStatus> {
  return request<SubscriptionStatus>('/payments/subscription-status', {}, true);
}

// Admin
export async function getSecurityChecklist(): Promise<ChecklistItem[]> {
  return request<ChecklistItem[]>('/admin/security-checklist', {}, true);
}

export async function getLegalReadiness(): Promise<ChecklistItem[]> {
  return request<ChecklistItem[]>('/admin/legal-readiness', {}, true);
}

export async function getLoadTestResults(): Promise<LoadTestResult[]> {
  return request<LoadTestResult[]>('/admin/load-test-results', {}, true);
}

// VA
export async function getVaMockProfile(): Promise<Record<string, unknown>> {
  return request('/va/mock/profile');
}

// Health
export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health');
}
