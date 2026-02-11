'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { leaseApi } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { LeaseWorkQueue } from '@/components/leases/LeaseWorkQueue';
import { AllLeasesTable } from '@/components/leases/AllLeasesTable';
import { UploadButton } from '@/components/leases/UploadButton';
import { Loader2, ListChecks, Table2 } from 'lucide-react';

type Tab = 'queue' | 'all';

export default function LeasesPage() {
  const { currentOrg } = useAuth();
  const [activeTab, setActiveTab] = useState<Tab>('queue');

  const { data: leases = [], isLoading, refetch } = useQuery({
    queryKey: ['leases', currentOrg?.id],
    queryFn: () => leaseApi.list(currentOrg?.id),
    enabled: !!currentOrg,
  });

  const reviewCount = leases.filter(
    (l) => l.status === 'completed' || l.status === 'processing' || l.status === 'failed'
  ).length;

  const tabs = [
    { key: 'queue' as Tab, label: 'Review Queue', icon: ListChecks, count: reviewCount },
    { key: 'all' as Tab, label: 'All Leases', icon: Table2, count: leases.length },
  ];

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Loader2 className="h-12 w-12 animate-spin text-amber-500" />
        <p className="mt-4 text-slate-600 font-medium">Loading leases...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Leases</h1>
          <p className="mt-1 text-sm text-slate-600">
            Review extractions and manage your lease documents
          </p>
        </div>
        <UploadButton onUploadComplete={refetch} />
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-slate-200">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? 'text-amber-700 border-b-2 border-amber-500 bg-amber-50/50'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
              <span
                className={`px-1.5 py-0.5 rounded-full text-xs font-medium ${
                  activeTab === tab.key
                    ? 'bg-amber-100 text-amber-700'
                    : 'bg-slate-100 text-slate-500'
                }`}
              >
                {tab.count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Content */}
      {activeTab === 'queue' ? (
        leases.length === 0 ? (
          <div className="text-center py-16 text-slate-500">
            <ListChecks className="w-12 h-12 mx-auto mb-3 text-slate-300" />
            <p className="font-medium">No leases to review</p>
            <p className="text-sm mt-1">Upload a lease PDF to get started</p>
          </div>
        ) : (
          <LeaseWorkQueue leases={leases} onUpdate={refetch} />
        )
      ) : (
        leases.length === 0 ? (
          <div className="text-center py-16 text-slate-500">
            <Table2 className="w-12 h-12 mx-auto mb-3 text-slate-300" />
            <p className="font-medium">No leases yet</p>
            <p className="text-sm mt-1">Upload a lease PDF to get started</p>
          </div>
        ) : (
          <AllLeasesTable leases={leases} onUpdate={refetch} />
        )
      )}
    </div>
  );
}
