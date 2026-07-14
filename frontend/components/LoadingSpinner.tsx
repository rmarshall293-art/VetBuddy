import { HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export function LoadingSpinner({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('flex items-center justify-center py-12', className)} {...props}>
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-cream-300 border-t-sage" />
    </div>
  );
}
