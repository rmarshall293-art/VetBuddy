'use client';

import { Jurisdiction } from '@/types';
import { cn } from '@/lib/utils';

interface JurisdictionSelectProps {
  jurisdictions: Jurisdiction[];
  value: string;
  onChange: (code: string) => void;
  label: string;
  id?: string;
  className?: string;
}

export function JurisdictionSelect({
  jurisdictions,
  value,
  onChange,
  label,
  id,
  className,
}: JurisdictionSelectProps) {
  const sorted = [...jurisdictions].sort((a, b) => a.name.localeCompare(b.name));

  return (
    <div className={cn('space-y-1.5', className)}>
      <label htmlFor={id} className="block text-sm font-medium text-navy-700">
        {label}
      </label>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-cream-300 bg-white px-4 py-2.5 text-navy focus:border-sage focus:outline-none focus:ring-2 focus:ring-sage/30"
      >
        <option value="">Select jurisdiction…</option>
        {sorted.map((j) => (
          <option key={j.code} value={j.code}>
            {j.name} ({j.code}) — {j.jurisdiction_type}
          </option>
        ))}
      </select>
    </div>
  );
}
