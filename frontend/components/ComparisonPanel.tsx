'use client';

import { ComparisonResult, COMPARISON_METRICS } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { MetricBadge } from './MetricBadge';
import { formatNumber } from '@/lib/utils';

interface ComparisonPanelProps {
  result: ComparisonResult;
  selectedMetrics: string[];
}

function formatMetricValue(key: string, val: unknown): string {
  if (val === null || val === undefined) return '—';
  if (typeof val === 'object') return JSON.stringify(val);
  if (
    ['veteran_population', 'gi_bill_usage_metric', 'housing_affordability_index'].includes(key)
  ) {
    return formatNumber(val as string | number);
  }
  return String(val);
}

export function ComparisonPanel({ result, selectedMetrics }: ComparisonPanelProps) {
  const { from_jurisdiction: from, to_jurisdiction: to, metrics, confidence, citations } = result;

  const activeMetrics =
    selectedMetrics.length > 0
      ? COMPARISON_METRICS.filter((m) => selectedMetrics.includes(m.key))
      : COMPARISON_METRICS;

  return (
    <div className="space-y-6">
      {result.placeholder_warning && (
        <div className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          <strong>Placeholder data warning:</strong> Some metrics use placeholder or unverified data.
          Verify with official state veterans agencies and VA sources before making decisions.
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>{from.name}</CardTitle>
            <p className="text-sm text-navy-400">
              {from.code} · {from.jurisdiction_type}
            </p>
          </CardHeader>
          <CardContent>
            <dl className="space-y-3 text-sm">
              {from.state_veterans_agency_name && (
                <div>
                  <dt className="font-medium text-navy-500">Veterans Agency</dt>
                  <dd className="text-navy-800">{from.state_veterans_agency_name}</dd>
                </div>
              )}
              {from.confidence_score && (
                <div>
                  <dt className="font-medium text-navy-500">Data Confidence</dt>
                  <dd>
                    <MetricBadge label="Overall" confidence={from.confidence_score} />
                  </dd>
                </div>
              )}
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{to.name}</CardTitle>
            <p className="text-sm text-navy-400">
              {to.code} · {to.jurisdiction_type}
            </p>
          </CardHeader>
          <CardContent>
            <dl className="space-y-3 text-sm">
              {to.state_veterans_agency_name && (
                <div>
                  <dt className="font-medium text-navy-500">Veterans Agency</dt>
                  <dd className="text-navy-800">{to.state_veterans_agency_name}</dd>
                </div>
              )}
              {to.confidence_score && (
                <div>
                  <dt className="font-medium text-navy-500">Data Confidence</dt>
                  <dd>
                    <MetricBadge label="Overall" confidence={to.confidence_score} />
                  </dd>
                </div>
              )}
            </dl>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Side-by-Side Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-cream-300 text-left">
                  <th className="pb-3 pr-4 font-medium text-navy-500">Metric</th>
                  <th className="pb-3 pr-4 font-medium text-navy">{from.code}</th>
                  <th className="pb-3 pr-4 font-medium text-navy">{to.code}</th>
                  <th className="pb-3 font-medium text-navy-500">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {activeMetrics.map((m) => {
                  const fromRecord = from as unknown as Record<string, unknown>;
                  const toRecord = to as unknown as Record<string, unknown>;
                  const fromVal =
                    metrics[`${m.key}_from`] ?? fromRecord[m.key];
                  const toVal =
                    metrics[`${m.key}_to`] ?? toRecord[m.key];
                  const conf = confidence?.[m.key];

                  return (
                    <tr key={m.key} className="border-b border-cream-200">
                      <td className="py-3 pr-4 font-medium text-navy-700">{m.label}</td>
                      <td className="py-3 pr-4 text-navy-800 max-w-xs">
                        {formatMetricValue(m.key, fromVal)}
                      </td>
                      <td className="py-3 pr-4 text-navy-800 max-w-xs">
                        {formatMetricValue(m.key, toVal)}
                      </td>
                      <td className="py-3">
                        {conf !== undefined ? (
                          <MetricBadge label="" confidence={conf} />
                        ) : (
                          '—'
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {result.alabama_quick_compare && (
        <Card className="border-sage-300 bg-sage-50/50">
          <CardHeader>
            <CardTitle>Alabama Quick Compare</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="overflow-x-auto text-xs text-navy-700">
              {JSON.stringify(result.alabama_quick_compare, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      {citations && citations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Citations</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              {citations.map((url, i) => (
                <li key={i}>
                  <a
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sage-600 underline hover:text-sage-700 break-all"
                  >
                    {url}
                  </a>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
