'use client';

import { ReactNode, useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LeaseSectionProps {
  title: string;
  count: number;
  icon: ReactNode;
  color: 'red' | 'blue' | 'amber' | 'green';
  defaultExpanded?: boolean;
  children: ReactNode;
}

const colorConfig = {
  red: {
    text: 'text-red-600',
    bg: 'bg-red-50',
    border: 'border-red-200',
    accent: 'text-red-700',
  },
  blue: {
    text: 'text-blue-600',
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    accent: 'text-blue-700',
  },
  amber: {
    text: 'text-amber-600',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    accent: 'text-amber-700',
  },
  green: {
    text: 'text-green-600',
    bg: 'bg-green-50',
    border: 'border-green-200',
    accent: 'text-green-700',
  },
};

export function LeaseSection({
  title,
  count,
  icon,
  color,
  defaultExpanded = true,
  children,
}: LeaseSectionProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const colors = colorConfig[color];

  return (
    <div className={cn('bg-white rounded-xl border shadow-sm overflow-hidden', colors.border)}>
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className={cn(
          'w-full px-6 py-4 flex items-center justify-between transition-colors',
          colors.bg,
          'hover:opacity-80'
        )}
      >
        <div className="flex items-center gap-3">
          <div className={colors.text}>{icon}</div>
          <h3 className={cn('text-lg font-bold', colors.accent)}>
            {title}
          </h3>
          <span
            className={cn(
              'px-2.5 py-0.5 rounded-full text-sm font-semibold',
              colors.bg,
              colors.text
            )}
          >
            {count}
          </span>
        </div>
        {expanded ? (
          <ChevronDown className={cn('w-5 h-5', colors.text)} />
        ) : (
          <ChevronRight className={cn('w-5 h-5', colors.text)} />
        )}
      </button>

      {/* Content */}
      {expanded && (
        <div className="divide-y divide-slate-100">
          {children}
        </div>
      )}
    </div>
  );
}
