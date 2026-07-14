import { cn, confidenceColor } from '@/lib/utils';

interface MetricBadgeProps {
  label: string;
  confidence?: string | number;
  className?: string;
}

export function MetricBadge({ label, confidence, className }: MetricBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium',
        confidenceColor(confidence),
        className,
      )}
    >
      <span
        className={cn(
          'h-1.5 w-1.5 rounded-full',
          confidence === 'high' || (typeof confidence === 'number' && confidence >= 0.8)
            ? 'bg-green-600'
            : confidence === 'medium' || (typeof confidence === 'number' && confidence >= 0.5)
              ? 'bg-amber-500'
              : 'bg-red-500',
        )}
      />
      {label}
      {confidence !== undefined && (
        <span className="opacity-75">
          ({typeof confidence === 'number' ? `${(confidence * 100).toFixed(0)}%` : confidence})
        </span>
      )}
    </span>
  );
}
