'use client';

import { useState, FormEvent } from 'react';
import { searchBenefits, listBenefits } from '@/lib/api';
import { PageHeader } from '@/components/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import type { Benefit } from '@/types';

export default function BenefitsPage() {
  const [query, setQuery] = useState('');
  const [jurisdiction, setJurisdiction] = useState('');
  const [results, setResults] = useState<Benefit[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState('');

  async function handleSearch(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSearched(true);
    try {
      const data = query.trim()
        ? await searchBenefits(query.trim())
        : await listBenefits({
            jurisdiction: jurisdiction || undefined,
          });
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6">
      <PageHeader
        title="Benefits Search"
        description="Search federal and state veteran benefits. Alabama pilot content with national coverage."
        badge="Educational"
      />

      <Card className="mb-8">
        <CardContent className="pt-6">
          <form onSubmit={handleSearch} className="space-y-4">
            <Input
              id="query"
              label="Search benefits"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. education, property tax, disability"
            />
            <Input
              id="jurisdiction"
              label="Jurisdiction code (optional)"
              value={jurisdiction}
              onChange={(e) => setJurisdiction(e.target.value.toUpperCase())}
              placeholder="AL, TX, CA…"
            />
            <Button type="submit" disabled={loading}>
              {loading ? 'Searching…' : 'Search Benefits'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {error && (
        <div className="mb-6 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      )}

      {loading && <LoadingSpinner />}

      {searched && !loading && (
        <>
          <p className="mb-4 text-sm text-navy-500">
            {results.length} result{results.length !== 1 ? 's' : ''}
          </p>
          {results.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-navy-500">
                No benefits found. Try a different search term or jurisdiction.
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {results.map((benefit) => (
                <Card key={benefit.id} hover>
                  <CardHeader>
                    <div className="flex items-start justify-between gap-4">
                      <CardTitle className="text-lg">{benefit.name}</CardTitle>
                      <span className="shrink-0 rounded-full bg-sage/15 px-2.5 py-0.5 text-xs font-medium text-sage-700">
                        {benefit.category}
                      </span>
                    </div>
                    {benefit.jurisdiction_code && (
                      <p className="text-xs text-navy-400">{benefit.jurisdiction_code}</p>
                    )}
                  </CardHeader>
                  <CardContent>
                    {benefit.summary && (
                      <p className="text-sm text-navy-600">{benefit.summary}</p>
                    )}
                    {benefit.eligibility && (
                      <p className="mt-2 text-xs text-navy-500">
                        <strong>Eligibility:</strong> {benefit.eligibility}
                      </p>
                    )}
                    {benefit.data_status === 'placeholder' && (
                      <p className="mt-2 text-xs text-amber-700">
                        Placeholder data — verify with official sources.
                      </p>
                    )}
                    {benefit.url && (
                      <a
                        href={benefit.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-2 inline-block text-sm text-sage-600 hover:underline"
                      >
                        Official source →
                      </a>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
