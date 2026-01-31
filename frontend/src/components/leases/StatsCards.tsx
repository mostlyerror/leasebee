'use client';

import { FileText, Clock, TrendingUp, Zap } from 'lucide-react';
import { StatsCard } from '@/components/ui/stats-card';

interface StatsCardsProps {
  totalLeases: number;
  processedLeases: number;
  timeSaved: number; // in minutes
}

function formatTime(minutes: number): string {
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
}

export function StatsCards({ totalLeases, processedLeases, timeSaved }: StatsCardsProps) {
  const accuracy = 94; // Mock - would calculate from actual data

  const stats = [
    {
      title: 'Total Documents',
      value: totalLeases,
      icon: <FileText className="w-6 h-6" />,
    },
    {
      title: 'Processed',
      value: processedLeases,
      icon: <TrendingUp className="w-6 h-6" />,
      change: {
        value: '+12% this month',
        trend: 'up' as const,
      },
    },
    {
      title: 'Time Saved',
      value: formatTime(timeSaved),
      icon: <Clock className="w-6 h-6" />,
    },
    {
      title: 'Avg. Accuracy',
      value: `${accuracy}%`,
      icon: <Zap className="w-6 h-6" />,
      change: {
        value: '+2.1% this month',
        trend: 'up' as const,
      },
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat) => (
        <StatsCard
          key={stat.title}
          title={stat.title}
          value={stat.value}
          icon={stat.icon}
          change={stat.change}
        />
      ))}
    </div>
  );
}
