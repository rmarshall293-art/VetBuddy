import { HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

interface PageHeaderProps extends HTMLAttributes<HTMLDivElement> {
  title: string;
  description?: string;
  badge?: string;
}

export function PageHeader({ title, description, badge, className, children, ...props }: PageHeaderProps) {
  return (
    <div className={cn('mb-8', className)} {...props}>
      {badge && (
        <span className="mb-3 inline-block rounded-full bg-sage/15 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-sage-700">
          {badge}
        </span>
      )}
      <h1 className="font-display text-3xl font-bold text-navy sm:text-4xl">{title}</h1>
      {description && (
        <p className="mt-2 max-w-2xl text-lg text-navy-500">{description}</p>
      )}
      {children}
    </div>
  );
}
