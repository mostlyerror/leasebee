'use client';

import { FileText, Clock, TrendingUp, Zap } from 'lucide-react';

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
      label: 'Total Documents',
      value: totalLeases,
      icon: FileText,
      color: 'bg-blue-500',
      lightColor: 'bg-blue-50',
      textColor: 'text-blue-600',
    },
    {
      label: 'Processed',
      value: processedLeases,
      icon: TrendingUp,
      color: 'bg-green-500',
      lightColor: 'bg-green-50',
      textColor: 'text-green-600',
    },
    {
      label: 'Time Saved',
      value: formatTime(timeSaved),
      icon: Clock,
      color: 'bg-amber-500',
      lightColor: 'bg-amber-50',
      textColor: 'text-amber-600',
    },
    {
      label: 'Avg. Accuracy',
      value: `${accuracy}%`,
      icon: Zap,
      color: 'bg-purple-500',
      lightColor: 'bg-purple-50',
      textColor: 'text-purple-600',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm hover:shadow-md transition-shadow"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-600">{stat.label}</p>
              <p className="mt-2 text-3xl font-bold text-slate-900">{stat.value}</p>
            </div>
            <div className={`${stat.lightColor} p-3 rounded-lg`}>
              <stat.icon className={`w-6 h-6 ${stat.textColor}`} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
