'use client';

import { ApiClientError } from '@/lib/api';

interface AuthGateProps {
  error?: string | null;
  children?: React.ReactNode;
}

export function AuthGate({ error, children }: AuthGateProps) {
  if (!error) return null;

  const is401 = error.includes('401') || error.toLowerCase().includes('unauthorized');

  return (
    <div className="rounded-xl border border-amber-300 bg-amber-50 px-6 py-8 text-center">
      <h3 className="font-display text-xl text-navy">
        {is401 ? 'Sign in required' : 'Unable to load data'}
      </h3>
      <p className="mt-2 text-navy-600">
        {is401
          ? 'Please log in to access this section. Your session may have expired.'
          : error}
      </p>
      {is401 && (
        <div className="mt-4 flex justify-center gap-3">
          <a
            href="/login"
            className="rounded-lg bg-navy px-5 py-2.5 text-sm font-semibold text-cream hover:bg-navy-600"
          >
            Log in
          </a>
          <a
            href="/register"
            className="rounded-lg border-2 border-navy px-5 py-2.5 text-sm font-semibold text-navy hover:bg-navy hover:text-cream"
          >
            Register
          </a>
        </div>
      )}
      {children}
    </div>
  );
}

export function getErrorMessage(err: unknown): string {
  if (err instanceof ApiClientError) return err.message;
  if (err instanceof Error) return err.message;
  return 'An unexpected error occurred';
}
