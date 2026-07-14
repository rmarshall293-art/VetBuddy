import { statusColor } from '@/lib/utils';
import { cn } from '@/lib/utils';

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium capitalize',
        statusColor(status),
        className,
      )}
    >
      {status.replace(/_/g, ' ')}
    </span>
  );
}
