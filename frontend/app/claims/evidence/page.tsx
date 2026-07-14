'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { listClaims } from '@/lib/api';
import { AuthGate, getErrorMessage } from '@/components/AuthGate';
import { PageHeader } from '@/components/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { StatusBadge } from '@/components/StatusBadge';

const EVIDENCE_TYPES = [
  {
    type: 'service_records',
    title: 'Service Treatment Records (STRs)',
    description: 'In-service medical records documenting symptoms, treatment, or injuries.',
    status: 'needed',
  },
  {
    type: 'dd214',
    title: 'DD-214 / Service Records',
    description: 'Proof of service, discharge characterization, and deployment history.',
    status: 'needed',
  },
  {
    type: 'nexus_letter',
    title: 'Nexus Letter / Medical Opinion',
    description: 'Provider statement linking current condition to military service.',
    status: 'needed',
  },
  {
    type: 'buddy_statement',
    title: 'Buddy / Lay Statements',
    description: 'Form 21-4138 or sworn statements from fellow service members or family.',
    status: 'needed',
  },
  {
    type: 'private_medical',
    title: 'Private Medical Records',
    description: 'Post-service treatment records, diagnoses, and imaging.',
    status: 'needed',
  },
  {
    type: 'va_exams',
    title: 'VA C&P Examination Results',
    description: 'Compensation & Pension exam findings if already scheduled.',
    status: 'needed',
  },
];

export default function EvidencePage() {
  const [claimEvidence, setClaimEvidence] = useState<{ title: string; items: typeof EVIDENCE_TYPES }[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listClaims()
      .then((claims) => {
        const mapped = claims.map((c) => ({
          title: c.title,
          items: c.evidence.length > 0
            ? c.evidence.map((e) => ({
                type: e.evidence_type,
                title: e.title,
                description: e.description || '',
                status: e.status,
              }))
            : EVIDENCE_TYPES,
        }));
        setClaimEvidence(mapped);
      })
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6">
      <PageHeader
        title="Evidence Checklist"
        description="Organize the evidence needed to support your VA disability claim. Educational guidance only."
        badge="Claims"
      />

      {error && (
        <div className="mb-6">
          <AuthGate error={error} />
        </div>
      )}

      <div className="mb-6 rounded-lg border border-cream-300 bg-cream-100 px-4 py-3 text-sm text-navy-600">
        Standard evidence categories for most disability claims. Your specific claim may require
        additional documentation.{' '}
        <Link href="/claims/forms" className="text-sage-600 underline">
          View VA Forms Guide
        </Link>
      </div>

      {claimEvidence.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>General Evidence Checklist</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {EVIDENCE_TYPES.map((item) => (
              <div
                key={item.type}
                className="flex items-start justify-between rounded-lg border border-cream-200 p-4"
              >
                <div>
                  <h4 className="font-semibold text-navy">{item.title}</h4>
                  <p className="mt-1 text-sm text-navy-500">{item.description}</p>
                </div>
                <StatusBadge status={item.status} />
              </div>
            ))}
          </CardContent>
        </Card>
      ) : (
        claimEvidence.map((claim, i) => (
          <Card key={i} className="mb-6">
            <CardHeader>
              <CardTitle>{claim.title}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {claim.items.map((item, j) => (
                <div
                  key={j}
                  className="flex items-start justify-between rounded-lg border border-cream-200 p-4"
                >
                  <div>
                    <h4 className="font-semibold text-navy">{item.title}</h4>
                    <p className="mt-1 text-sm text-navy-500">{item.description}</p>
                  </div>
                  <StatusBadge status={item.status} />
                </div>
              ))}
            </CardContent>
          </Card>
        ))
      )}
    </div>
  );
}
