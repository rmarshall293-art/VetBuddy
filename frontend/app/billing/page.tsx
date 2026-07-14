'use client';

import { useEffect, useState } from 'react';
import { createCheckoutSession, getSubscriptionStatus } from '@/lib/api';
import { AuthGate, getErrorMessage } from '@/components/AuthGate';
import { PageHeader } from '@/components/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import type { SubscriptionStatus } from '@/types';
import { formatDate } from '@/lib/utils';

const FEATURES = [
  'Unlimited claims workspace',
  '56-jurisdiction comparison',
  'Alabama resource center access',
  'Evidence checklist & ITF guide',
  'Benefits search',
  'VA forms educational guide',
  'Priority support (coming soon)',
];

export default function BillingPage() {
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  useEffect(() => {
    getSubscriptionStatus()
      .then(setSubscription)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  async function handleSubscribe() {
    setCheckoutLoading(true);
    try {
      const session = await createCheckoutSession();
      if (session.checkout_url) {
        window.location.href = session.checkout_url;
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setCheckoutLoading(false);
    }
  }

  const price = subscription?.price_cents ? (subscription.price_cents / 100).toFixed(2) : '5.99';

  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <PageHeader
        title="VetBuddy Subscription"
        description="Full access to claims tools, jurisdiction comparison, and Alabama veteran resources."
      />

      {loading ? (
        <LoadingSpinner />
      ) : error ? (
        <AuthGate error={error} />
      ) : (
        <>
          <Card className="mb-8 border-sage-300 bg-gradient-to-br from-white to-sage-50/30">
            <CardHeader className="text-center">
              <p className="text-sm font-semibold uppercase tracking-widest text-sage-600">
                Veteran Benefits Platform
              </p>
              <CardTitle className="text-4xl">
                <span className="font-display">${price}</span>
                <span className="text-lg font-normal text-navy-500">/month</span>
              </CardTitle>
              <p className="text-navy-500">
                Current status:{' '}
                <span className="font-semibold capitalize text-navy">{subscription?.status}</span>
                {subscription?.current_period_end && (
                  <> · Renews {formatDate(subscription.current_period_end)}</>
                )}
              </p>
            </CardHeader>
            <CardContent>
              <ul className="mb-8 space-y-3">
                {FEATURES.map((f) => (
                  <li key={f} className="flex items-center gap-3 text-navy-700">
                    <svg className="h-5 w-5 shrink-0 text-sage" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    {f}
                  </li>
                ))}
              </ul>
              <Button
                className="w-full"
                size="lg"
                onClick={handleSubscribe}
                disabled={checkoutLoading || subscription?.status === 'active'}
              >
                {checkoutLoading
                  ? 'Redirecting to checkout…'
                  : subscription?.status === 'active'
                    ? 'Subscribed'
                    : 'Subscribe Now'}
              </Button>
              <p className="mt-4 text-center text-xs text-navy-400">
                Educational guidance only — not legal advice. Cancel anytime. Secure payment via Stripe.
              </p>
            </CardContent>
          </Card>

          <div className="rounded-lg border border-cream-300 bg-cream-100 px-4 py-3 text-sm text-navy-600 text-center">
            Alabama veterans: start with our free pilot resources, then upgrade for full comparison tools.
          </div>
        </>
      )}
    </div>
  );
}
