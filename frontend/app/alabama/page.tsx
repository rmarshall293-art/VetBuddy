'use client';

import { useEffect, useState } from 'react';
import {
  getAlabamaBenefits,
  getAlabamaTraining,
  getAlabamaOffices,
  getAlabamaRanking,
} from '@/lib/api';
import { PageHeader } from '@/components/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { MetricBadge } from '@/components/MetricBadge';

export default function AlabamaPage() {
  const [benefits, setBenefits] = useState<unknown[]>([]);
  const [training, setTraining] = useState<Record<string, unknown> | null>(null);
  const [offices, setOffices] = useState<unknown[]>([]);
  const [ranking, setRanking] = useState<Record<string, unknown> | null>(null);
  const [disclaimer, setDisclaimer] = useState('');
  const [placeholderWarning, setPlaceholderWarning] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'benefits' | 'offices' | 'training' | 'ranking'>('benefits');

  useEffect(() => {
    Promise.all([
      getAlabamaBenefits(),
      getAlabamaTraining(),
      getAlabamaOffices(),
      getAlabamaRanking(),
    ])
      .then(([benefitsData, trainingData, officesData, rankingData]) => {
        setBenefits(benefitsData.benefits);
        setDisclaimer(benefitsData.disclaimer);
        setPlaceholderWarning(benefitsData.placeholder_warning);
        setTraining(trainingData);
        setOffices(officesData.offices);
        setRanking(rankingData);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;

  const tabs = [
    { id: 'benefits' as const, label: 'Benefits' },
    { id: 'offices' as const, label: 'County Offices' },
    { id: 'training' as const, label: 'Resource Officer Training' },
    { id: 'ranking' as const, label: 'Ranking' },
  ];

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <PageHeader
        title="Alabama Veteran Resource Center"
        description="Deep-dive Alabama benefits, county VSO offices, resource officer training, and state ranking metrics."
        badge="Pilot Jurisdiction"
      />

      {placeholderWarning && (
        <div className="mb-6 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          <strong>Placeholder data warning:</strong> Verify all Alabama benefits and office information
          with ADVA and county veterans service officers before making decisions.
        </div>
      )}

      {disclaimer && (
        <div className="mb-6 rounded-lg border border-cream-300 bg-cream-100 px-4 py-3 text-sm text-navy-600">
          {disclaimer}
        </div>
      )}

      <div className="mb-6 flex flex-wrap gap-2 border-b border-cream-300 pb-4">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-navy text-cream'
                : 'text-navy-600 hover:bg-navy-50'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'benefits' && (
        <div className="grid gap-4 sm:grid-cols-2">
          {(benefits as Array<Record<string, string>>).map((b, i) => (
            <Card key={i} hover>
              <CardHeader>
                <CardTitle>{b.name || b.title}</CardTitle>
                {b.category && (
                  <p className="text-xs font-medium uppercase tracking-wider text-sage-600">
                    {b.category}
                  </p>
                )}
              </CardHeader>
              <CardContent>
                <p className="text-sm text-navy-600">{b.summary || b.description}</p>
                {b.eligibility && (
                  <p className="mt-2 text-xs text-navy-500">
                    <strong>Eligibility:</strong> {b.eligibility}
                  </p>
                )}
                {b.url && (
                  <a
                    href={b.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-2 inline-block text-sm text-sage-600 hover:underline"
                  >
                    Learn more →
                  </a>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {activeTab === 'offices' && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {(offices as Array<Record<string, string>>).map((office, i) => (
            <Card key={office.id || i}>
              <CardHeader>
                <CardTitle className="text-lg">{office.name}</CardTitle>
                {office.facility_type && (
                  <p className="text-xs text-navy-400 capitalize">{office.facility_type}</p>
                )}
              </CardHeader>
              <CardContent className="text-sm text-navy-600 space-y-1">
                {office.city && <p>{office.city}</p>}
                {office.address && <p>{office.address}</p>}
                {office.phone && <p>{office.phone}</p>}
                {office.url && (
                  <a href={office.url} className="text-sage-600 hover:underline" target="_blank" rel="noopener noreferrer">
                    Website →
                  </a>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {activeTab === 'training' && training && (
        <div className="space-y-6">
          {Object.entries(training).map(([key, level]) => {
            if (typeof level !== 'object' || level === null) return null;
            const l = level as { title?: string; modules?: string[]; quiz?: Array<{ q: string; choices: string[]; answer: number }> };
            return (
              <Card key={key}>
                <CardHeader>
                  <CardTitle>{l.title || key}</CardTitle>
                </CardHeader>
                <CardContent>
                  {l.modules && (
                    <ul className="list-disc pl-5 space-y-1 text-sm text-navy-600">
                      {l.modules.map((m, i) => (
                        <li key={i}>{m}</li>
                      ))}
                    </ul>
                  )}
                  {l.quiz && l.quiz.length > 0 && (
                    <div className="mt-4 border-t border-cream-200 pt-4">
                      <p className="text-sm font-medium text-navy-700 mb-2">Sample quiz questions</p>
                      {l.quiz.map((q, i) => (
                        <div key={i} className="mb-3 text-sm">
                          <p className="font-medium text-navy">{q.q}</p>
                          <ul className="mt-1 pl-4 text-navy-500">
                            {q.choices.map((c, j) => (
                              <li key={j} className={j === q.answer ? 'text-sage-700 font-medium' : ''}>
                                {c}
                              </li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {activeTab === 'ranking' && ranking && (
        <Card>
          <CardHeader>
            <CardTitle>Alabama Ranking Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {Object.entries(ranking).map(([key, val]) => {
                if (typeof val === 'object') return null;
                return (
                  <div key={key} className="rounded-lg border border-cream-200 p-4">
                    <p className="text-xs font-medium uppercase tracking-wider text-navy-400">
                      {key.replace(/_/g, ' ')}
                    </p>
                    <p className="mt-1 font-display text-2xl font-bold text-navy">{String(val)}</p>
                  </div>
                );
              })}
            </div>
            {Array.isArray(ranking.metrics) && (ranking.metrics as Array<Record<string, unknown>>).length > 0 && (
              <div className="mt-6 space-y-3">
                {(ranking.metrics as Array<Record<string, unknown>>).map((m, i) => (
                  <div key={i} className="flex items-center justify-between rounded-lg bg-cream-100 px-4 py-3">
                    <span className="text-sm text-navy-700">{String(m.name || m.metric)}</span>
                    <MetricBadge
                      label={String(m.score ?? m.value ?? '')}
                      confidence={m.confidence as string | number | undefined}
                    />
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
