import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateStr?: string | null): string {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatNumber(val?: string | number | null): string {
  if (val === null || val === undefined) return '—';
  const n = typeof val === 'string' ? parseFloat(val) : val;
  if (isNaN(n)) return String(val);
  return n.toLocaleString('en-US');
}

export function confidenceColor(level?: string | number): string {
  if (!level) return 'bg-sage-100 text-sage-700';
  const s = String(level).toLowerCase();
  if (s === 'high' || (typeof level === 'number' && level >= 0.8)) {
    return 'bg-green-100 text-green-800';
  }
  if (s === 'medium' || (typeof level === 'number' && level >= 0.5)) {
    return 'bg-amber-100 text-amber-800';
  }
  return 'bg-red-100 text-red-800';
}

export function statusColor(status: string): string {
  const map: Record<string, string> = {
    draft: 'bg-sage-100 text-sage-700',
    submitted: 'bg-blue-100 text-blue-800',
    in_review: 'bg-amber-100 text-amber-800',
    approved: 'bg-green-100 text-green-800',
    denied: 'bg-red-100 text-red-800',
    complete: 'bg-green-100 text-green-800',
    in_progress: 'bg-blue-100 text-blue-800',
    not_started: 'bg-cream-200 text-navy-600',
    needed: 'bg-amber-100 text-amber-800',
    collected: 'bg-green-100 text-green-800',
  };
  return map[status] || 'bg-cream-200 text-navy-600';
}
