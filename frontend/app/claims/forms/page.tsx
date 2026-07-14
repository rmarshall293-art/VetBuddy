'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { listForms } from '@/lib/api';
import { PageHeader } from '@/components/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import type { VaForm } from '@/types';

export default function FormsPage() {
  const [forms, setForms] = useState<VaForm[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    listForms()
      .then(setForms)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load forms'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6">
      <PageHeader
        title="VA Forms Guide"
        description="Educational overview of commonly used VA forms. Always use official VA.gov forms for submission."
        badge="Educational — Not Legal Advice"
      />

      {error && (
        <div className="mb-6 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      )}

      <div className="mb-6 rounded-lg border border-cream-300 bg-cream-100 px-4 py-3 text-sm text-navy-600">
        Need to preserve your effective date? See our{' '}
        <Link href="/claims/intent-to-file" className="text-sage-600 underline">
          Intent to File guide
        </Link>
        .
      </div>

      <div className="space-y-4">
        {forms.map((form) => (
          <Card key={form.id} hover>
            <CardHeader>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-mono text-sage-600">{form.form_number}</p>
                  <CardTitle>{form.title}</CardTitle>
                </div>
                {form.category && (
                  <span className="shrink-0 rounded-full bg-sage/15 px-3 py-1 text-xs font-medium text-sage-700 capitalize">
                    {form.category.replace(/_/g, ' ')}
                  </span>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {form.description && (
                <p className="text-navy-600">{form.description}</p>
              )}
              {form.guidance && (
                <p className="mt-2 text-sm text-navy-500">{form.guidance}</p>
              )}
              {form.url && (
                <a
                  href={form.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-3 inline-block text-sm font-semibold text-sage-600 hover:underline"
                >
                  View on VA.gov →
                </a>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
