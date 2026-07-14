import { ChecklistItem } from '@/types';
import { statusColor } from '@/lib/utils';
import { cn } from '@/lib/utils';

interface ChecklistTableProps {
  items: ChecklistItem[];
  title: string;
}

export function ChecklistTable({ items, title }: ChecklistTableProps) {
  const statusCounts = items.reduce(
    (acc, item) => {
      acc[item.status] = (acc[item.status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-4">
        <h3 className="font-display text-xl text-navy">{title}</h3>
        <div className="flex gap-2 text-xs">
          {Object.entries(statusCounts).map(([status, count]) => (
            <span
              key={status}
              className={cn('rounded-full px-2.5 py-0.5 font-medium', statusColor(status))}
            >
              {status.replace(/_/g, ' ')}: {count}
            </span>
          ))}
        </div>
      </div>
      <div className="overflow-x-auto rounded-xl border border-cream-300">
        <table className="w-full text-sm">
          <thead className="bg-cream-100">
            <tr className="text-left">
              <th className="px-4 py-3 font-medium text-navy-600">Code</th>
              <th className="px-4 py-3 font-medium text-navy-600">Item</th>
              <th className="px-4 py-3 font-medium text-navy-600">Status</th>
              <th className="px-4 py-3 font-medium text-navy-600">Notes</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="border-t border-cream-200">
                <td className="px-4 py-3 font-mono text-xs text-navy-500">{item.code}</td>
                <td className="px-4 py-3 text-navy-800">{item.title}</td>
                <td className="px-4 py-3">
                  <span
                    className={cn(
                      'rounded-full px-2.5 py-0.5 text-xs font-medium',
                      statusColor(item.status),
                    )}
                  >
                    {item.status.replace(/_/g, ' ')}
                  </span>
                </td>
                <td className="px-4 py-3 text-navy-600">{item.notes || item.value || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
