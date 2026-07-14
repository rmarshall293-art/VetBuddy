'use client';

import { useEffect, useState } from 'react';
import { getSecurityChecklist, getLegalReadiness, getLoadTestResults } from '@/lib/api';
import { AuthGate, getErrorMessage } from '@/components/AuthGate';
import { ChecklistTable } from '@/components/ChecklistTable';
import { PageHeader } from '@/components/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import type { ChecklistItem, LoadTestResult } from '@/types';
import { formatNumber } from '@/lib/utils';

export default function AdminPage() {
  const [security, setSecurity] = useState<ChecklistItem[]>([]);
  const [legal, setLegal] = useState<ChecklistItem[]>([]);
  const [loadTests, setLoadTests] = useState<LoadTestResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getSecurityChecklist(), getLegalReadiness(), getLoadTestResults()])
      .then(([sec, leg, load]) => {
        setSecurity(sec);
        setLegal(leg);
        setLoadTests(load);
      })
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-12">
        <PageHeader title="Admin Dashboard" description="Security, legal readiness, and load test monitoring." />
        <AuthGate error={error} />
      </div>
    );
  }

  const securityComplete = security.filter((i) => i.status === 'complete').length;
  const legalComplete = legal.filter((i) => i.status === 'complete').length;

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <PageHeader
        title="Admin Dashboard"
        description="Security checklist, legal contracting readiness, and load test results."
        badge="Admin Only"
      />

      <div className="mb-8 grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-navy-500">Security Checklist</p>
            <p className="font-display text-3xl font-bold text-navy">
              {securityComplete}/{security.length}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-navy-500">Legal Readiness</p>
            <p className="font-display text-3xl font-bold text-navy">
              {legalComplete}/{legal.length}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-navy-500">Load Test Runs</p>
            <p className="font-display text-3xl font-bold text-navy">{loadTests.length}</p>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-10">
        <ChecklistTable items={security} title="Security Checklist (NIST 800-53 aligned)" />
        <ChecklistTable items={legal} title="Legal & Contracting Readiness" />

        <div>
          <h3 className="mb-4 font-display text-xl text-navy">Load Test Results</h3>
          {loadTests.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-navy-500">
                No load test results recorded yet.
              </CardContent>
            </Card>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-cream-300">
              <table className="w-full text-sm">
                <thead className="bg-cream-100">
                  <tr className="text-left">
                    <th className="px-4 py-3 font-medium text-navy-600">Run</th>
                    <th className="px-4 py-3 font-medium text-navy-600">Tool</th>
                    <th className="px-4 py-3 font-medium text-navy-600">Users</th>
                    <th className="px-4 py-3 font-medium text-navy-600">Requests</th>
                    <th className="px-4 py-3 font-medium text-navy-600">Failure Rate</th>
                    <th className="px-4 py-3 font-medium text-navy-600">P95 (ms)</th>
                  </tr>
                </thead>
                <tbody>
                  {loadTests.map((run) => (
                    <tr key={run.id} className="border-t border-cream-200">
                      <td className="px-4 py-3 text-navy-800">{run.run_name}</td>
                      <td className="px-4 py-3 text-navy-600">{run.tool}</td>
                      <td className="px-4 py-3">{formatNumber(run.concurrent_users)}</td>
                      <td className="px-4 py-3">{formatNumber(run.total_requests)}</td>
                      <td className="px-4 py-3">
                        {run.failure_rate != null ? `${run.failure_rate}%` : '—'}
                      </td>
                      <td className="px-4 py-3">{formatNumber(run.p95_latency_ms)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
