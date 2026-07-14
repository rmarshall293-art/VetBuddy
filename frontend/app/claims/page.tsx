'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { listClaims, createClaim } from '@/lib/api';
import { AuthGate, getErrorMessage } from '@/components/AuthGate';
import { PageHeader } from '@/components/PageHeader';
import { Card, CardContent } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { StatusBadge } from '@/components/StatusBadge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import type { Claim } from '@/types';
import { formatDate } from '@/lib/utils';

export default function ClaimsPage() {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showNew, setShowNew] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    listClaims()
      .then(setClaims)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  async function handleCreate() {
    if (!newTitle.trim()) return;
    setCreating(true);
    try {
      const claim = await createClaim({
        title: newTitle,
        disclaimer_acknowledged: true,
      });
      setClaims((prev) => [claim, ...prev]);
      setNewTitle('');
      setShowNew(false);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setCreating(false);
    }
  }

  if (loading) return <LoadingSpinner />;
  if (error && claims.length === 0) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-12">
        <AuthGate error={error} />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <PageHeader
        title="Claims Dashboard"
        description="Organize disability claims, track evidence, and manage your intent-to-file timeline."
      >
        <div className="mt-4 flex flex-wrap gap-3">
          <Link href="/claims/intent-to-file">
            <Button variant="outline" size="sm">Intent to File</Button>
          </Link>
          <Link href="/claims/evidence">
            <Button variant="outline" size="sm">Evidence Checklist</Button>
          </Link>
          <Link href="/claims/forms">
            <Button variant="outline" size="sm">VA Forms</Button>
          </Link>
        </div>
      </PageHeader>

      <div className="mb-6 flex justify-between items-center">
        <p className="text-navy-500">{claims.length} claim{claims.length !== 1 ? 's' : ''}</p>
        <Button onClick={() => setShowNew(!showNew)}>+ New Claim</Button>
      </div>

      {showNew && (
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex gap-3">
              <Input
                id="claimTitle"
                label="Claim title"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="e.g. PTSD — Gulf War era"
                className="flex-1"
              />
              <div className="flex items-end gap-2">
                <Button onClick={handleCreate} disabled={creating}>
                  {creating ? 'Creating…' : 'Create'}
                </Button>
                <Button variant="ghost" onClick={() => setShowNew(false)}>Cancel</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {claims.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-navy-500">No claims yet. Create your first claim to get started.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {claims.map((claim) => (
            <Link key={claim.id} href={`/claims/${claim.id}`}>
              <Card hover className="transition-all hover:border-sage">
                <CardContent className="flex items-center justify-between py-5">
                  <div>
                    <h3 className="font-display text-lg font-bold text-navy">{claim.title}</h3>
                    <p className="text-sm text-navy-400">
                      {claim.claim_type} · Created {formatDate(claim.created_at)}
                      {claim.intent_to_file_date && ` · ITF ${formatDate(claim.intent_to_file_date)}`}
                    </p>
                    {claim.conditions.length > 0 && (
                      <p className="mt-1 text-xs text-navy-500">
                        {claim.conditions.length} condition{claim.conditions.length !== 1 ? 's' : ''}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    {claim.evidence_strength_score && (
                      <span className="text-sm text-sage-600">
                        Evidence: {claim.evidence_strength_score}
                      </span>
                    )}
                    <StatusBadge status={claim.status} />
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
