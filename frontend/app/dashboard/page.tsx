'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getMe, listClaims, getHealth, getVaMockProfile, getSubscriptionStatus } from '@/lib/api';
import { AuthGate, getErrorMessage } from '@/components/AuthGate';
import { PageHeader } from '@/components/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { StatusBadge } from '@/components/StatusBadge';
import { Button } from '@/components/ui/Button';
import type { User, Claim, HealthResponse, SubscriptionStatus } from '@/types';
import { formatDate } from '@/lib/utils';

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [vaProfile, setVaProfile] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [me, healthData] = await Promise.all([getMe(), getHealth()]);
        setUser(me);
        setHealth(healthData);

        try {
          const [claimsData, subData, profile] = await Promise.all([
            listClaims(),
            getSubscriptionStatus(),
            getVaMockProfile(),
          ]);
          setClaims(claimsData);
          setSubscription(subData);
          setVaProfile(profile);
        } catch {
          // partial load ok
        }
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="mx-auto max-w-4xl px-4 py-12"><AuthGate error={error} /></div>;

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <PageHeader
        title={`Welcome, ${user?.profile?.display_name || user?.email?.split('@')[0] || 'Veteran'}`}
        description="Your VetBuddy command center for claims, benefits, and jurisdiction insights."
        badge={user?.profile?.preferred_jurisdiction === 'AL' ? 'Alabama Pilot' : undefined}
      />

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-navy-500">Active Claims</p>
            <p className="font-display text-3xl font-bold text-navy">{claims.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-navy-500">Subscription</p>
            <p className="font-display text-3xl font-bold text-navy capitalize">
              {subscription?.status || 'free'}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-navy-500">API Status</p>
            <p className="font-display text-3xl font-bold text-sage-600 capitalize">
              {health?.status || '—'}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-navy-500">VA Mode</p>
            <p className="font-display text-3xl font-bold text-navy capitalize">
              {health?.va_mode || '—'}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Claims</CardTitle>
            <Link href="/claims">
              <Button size="sm" variant="outline">View All</Button>
            </Link>
          </CardHeader>
          <CardContent>
            {claims.length === 0 ? (
              <p className="text-navy-500 text-sm">No claims yet. Start organizing your first claim.</p>
            ) : (
              <ul className="space-y-3">
                {claims.slice(0, 5).map((claim) => (
                  <li key={claim.id}>
                    <Link
                      href={`/claims/${claim.id}`}
                      className="flex items-center justify-between rounded-lg border border-cream-200 px-4 py-3 hover:border-sage transition-colors"
                    >
                      <div>
                        <p className="font-medium text-navy">{claim.title}</p>
                        <p className="text-xs text-navy-400">{formatDate(claim.created_at)}</p>
                      </div>
                      <StatusBadge status={claim.status} />
                    </Link>
                  </li>
                ))}
              </ul>
            )}
            <Link href="/claims" className="mt-4 block">
              <Button className="w-full" variant="secondary">+ New Claim</Button>
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3">
            {[
              { href: '/state-comparison', label: 'Compare Jurisdictions' },
              { href: '/alabama', label: 'Alabama Resources' },
              { href: '/claims/intent-to-file', label: 'Intent to File Guide' },
              { href: '/claims/evidence', label: 'Evidence Checklist' },
              { href: '/benefits', label: 'Search Benefits' },
              { href: '/billing', label: 'Manage Subscription' },
            ].map((action) => (
              <Link
                key={action.href}
                href={action.href}
                className="rounded-lg border border-cream-200 px-4 py-3 text-navy hover:border-sage hover:bg-sage/5 transition-colors"
              >
                {action.label} →
              </Link>
            ))}
          </CardContent>
        </Card>
      </div>

      {vaProfile && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>VA Profile Preview (Mock)</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="overflow-x-auto rounded-lg bg-cream-100 p-4 text-xs text-navy-700">
              {JSON.stringify(vaProfile, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
