'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { getClaim } from '@/lib/api';
import { AuthGate, getErrorMessage } from '@/components/AuthGate';
import { PageHeader } from '@/components/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { StatusBadge } from '@/components/StatusBadge';
import { Button } from '@/components/ui/Button';
import type { Claim } from '@/types';
import { formatDate } from '@/lib/utils';

export default function ClaimDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [claim, setClaim] = useState<Claim | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    getClaim(id)
      .then(setClaim)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="mx-auto max-w-4xl px-4 py-12"><AuthGate error={error} /></div>;
  if (!claim) return null;

  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6">
      <div className="mb-4">
        <Link href="/claims" className="text-sm text-sage-600 hover:underline">← Back to Claims</Link>
      </div>

      <PageHeader title={claim.title}>
        <div className="mt-3 flex flex-wrap gap-3">
          <StatusBadge status={claim.status} />
          <span className="text-sm text-navy-500 capitalize">{claim.claim_type}</span>
        </div>
      </PageHeader>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Claim Details</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-4 sm:grid-cols-2 text-sm">
              <div>
                <dt className="font-medium text-navy-500">Created</dt>
                <dd className="text-navy-800">{formatDate(claim.created_at)}</dd>
              </div>
              <div>
                <dt className="font-medium text-navy-500">Intent to File</dt>
                <dd className="text-navy-800">{formatDate(claim.intent_to_file_date)}</dd>
              </div>
              <div>
                <dt className="font-medium text-navy-500">Evidence Strength</dt>
                <dd className="text-navy-800">{claim.evidence_strength_score || '—'}</dd>
              </div>
              <div>
                <dt className="font-medium text-navy-500">Appeal Path</dt>
                <dd className="text-navy-800">{claim.appeal_path || '—'}</dd>
              </div>
            </dl>
            {claim.notes && (
              <div className="mt-4 rounded-lg bg-cream-100 p-4 text-sm text-navy-700">
                {claim.notes}
              </div>
            )}
          </CardContent>
        </Card>

        {claim.conditions.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Conditions ({claim.conditions.length})</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {claim.conditions.map((c, i) => (
                <div key={c.id || i} className="rounded-lg border border-cream-200 p-4">
                  <h4 className="font-semibold text-navy">{c.condition_name}</h4>
                  {c.current_diagnosis && (
                    <p className="mt-1 text-sm text-navy-600">Diagnosis: {c.current_diagnosis}</p>
                  )}
                  {c.claimed_rating && (
                    <p className="text-sm text-navy-500">Claimed rating: {c.claimed_rating}%</p>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Evidence ({claim.evidence.length})</CardTitle>
            <Link href="/claims/evidence">
              <Button size="sm" variant="outline">Evidence Guide</Button>
            </Link>
          </CardHeader>
          <CardContent>
            {claim.evidence.length === 0 ? (
              <p className="text-sm text-navy-500">No evidence items tracked yet.</p>
            ) : (
              <ul className="space-y-2">
                {claim.evidence.map((e) => (
                  <li
                    key={e.id}
                    className="flex items-center justify-between rounded-lg border border-cream-200 px-4 py-3"
                  >
                    <div>
                      <p className="font-medium text-navy">{e.title}</p>
                      <p className="text-xs text-navy-400">{e.evidence_type}</p>
                    </div>
                    <StatusBadge status={e.status} />
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        {claim.missing_evidence_warnings != null && (
          <div className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            <strong>Missing evidence warnings:</strong>
            <pre className="mt-2 text-xs">{JSON.stringify(claim.missing_evidence_warnings, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
