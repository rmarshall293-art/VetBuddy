'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getIntentToFileChecklist } from '@/lib/api';
import { PageHeader } from '@/components/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { Button } from '@/components/ui/Button';
import type { IntentToFileChecklist } from '@/types';

export default function IntentToFilePage() {
  const [checklist, setChecklist] = useState<IntentToFileChecklist | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getIntentToFileChecklist()
      .then(setChecklist)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <PageHeader
        title="Intent to File Guide"
        description="Preserve your potential effective date while you gather evidence. Form VA 21-0966."
        badge="Educational"
      />

      {error && (
        <div className="mb-6 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      )}

      {checklist && (
        <>
          <div className="mb-6 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            {checklist.disclaimer}
          </div>

          <div className="space-y-4">
            {checklist.steps.map((step, idx) => (
              <Card key={step.id ?? step.step ?? idx}>
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-full bg-navy text-sm font-bold text-cream">
                      {step.id ?? step.step ?? idx + 1}
                    </span>
                    <CardTitle>{step.title}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-navy-600">{step.detail ?? step.description}</p>
                  {step.form && (
                    <p className="mt-2 text-sm font-medium text-sage-600">Form: {step.form}</p>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}

      <div className="mt-8 flex flex-wrap gap-3">
        <Link href="/claims/forms">
          <Button variant="outline">VA Forms Guide</Button>
        </Link>
        <Link href="/claims">
          <Button>Go to Claims</Button>
        </Link>
        <a
          href="https://www.va.gov/find-forms/about-form-21-0966/"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Button variant="ghost">Official VA Form 21-0966 →</Button>
        </a>
      </div>
    </div>
  );
}
