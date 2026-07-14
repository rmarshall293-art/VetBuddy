'use client';

import { useEffect, useState } from 'react';
import { listStates, compareStates, customCompare } from '@/lib/api';
import { JurisdictionSelect } from '@/components/JurisdictionSelect';
import { ComparisonPanel } from '@/components/ComparisonPanel';
import { PageHeader } from '@/components/PageHeader';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { Button } from '@/components/ui/Button';
import { COMPARISON_METRICS, type Jurisdiction, type ComparisonResult } from '@/types';

export default function StateComparisonPage() {
  const [jurisdictions, setJurisdictions] = useState<Jurisdiction[]>([]);
  const [fromCode, setFromCode] = useState('AL');
  const [toCode, setToCode] = useState('TX');
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([]);
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    listStates()
      .then(setJurisdictions)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load jurisdictions'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (fromCode && toCode && jurisdictions.length > 0) {
      handleCompare();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleCompare() {
    if (!fromCode || !toCode) return;
    setComparing(true);
    setError('');
    try {
      const data =
        selectedMetrics.length > 0
          ? await customCompare({ from_code: fromCode, to_code: toCode, metrics: selectedMetrics })
          : await compareStates(fromCode, toCode);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Comparison failed');
    } finally {
      setComparing(false);
    }
  }

  function toggleMetric(key: string) {
    setSelectedMetrics((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key],
    );
  }

  function alabamaQuickCompare(target: string) {
    setFromCode('AL');
    setToCode(target);
    setTimeout(() => handleCompare(), 0);
  }

  if (loading) return <LoadingSpinner />;

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <PageHeader
        title="56-Jurisdiction Comparison"
        description="Compare veteran-relevant metrics across any state, territory, or district. Alabama pilot with national reach."
        badge="National Capability"
      />

      <div className="mb-8 rounded-xl border border-cream-300 bg-white/60 p-6 backdrop-blur-sm">
        <div className="grid gap-6 lg:grid-cols-2">
          <JurisdictionSelect
            id="from"
            label="Starting jurisdiction"
            jurisdictions={jurisdictions}
            value={fromCode}
            onChange={setFromCode}
          />
          <JurisdictionSelect
            id="to"
            label="Comparison jurisdiction"
            jurisdictions={jurisdictions}
            value={toCode}
            onChange={setToCode}
          />
        </div>

        <div className="mt-6">
          <p className="mb-3 text-sm font-medium text-navy-700">Metric filters</p>
          <div className="flex flex-wrap gap-2">
            {COMPARISON_METRICS.map((m) => (
              <button
                key={m.key}
                onClick={() => toggleMetric(m.key)}
                className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                  selectedMetrics.includes(m.key)
                    ? 'bg-navy text-cream'
                    : 'bg-cream-200 text-navy-600 hover:bg-sage/20'
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-6 flex flex-wrap gap-3">
          <Button onClick={handleCompare} disabled={comparing || !fromCode || !toCode}>
            {comparing ? 'Comparing…' : 'Compare'}
          </Button>
        </div>

        <div className="mt-6 border-t border-cream-300 pt-6">
          <p className="mb-3 text-sm font-medium text-navy-700">Alabama quick compare</p>
          <div className="flex flex-wrap gap-2">
            {['FL', 'GA', 'TN', 'MS', 'TX', 'CA', 'AK', 'PR'].map((code) => {
              const j = jurisdictions.find((x) => x.code === code);
              return (
                <button
                  key={code}
                  onClick={() => alabamaQuickCompare(code)}
                  className="rounded-lg border border-sage/30 bg-sage/10 px-3 py-1.5 text-sm text-sage-700 hover:bg-sage/20 transition-colors"
                >
                  AL vs {j?.name || code}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      )}

      {result && <ComparisonPanel result={result} selectedMetrics={selectedMetrics} />}
    </div>
  );
}
