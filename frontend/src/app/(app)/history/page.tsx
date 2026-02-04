'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { leaseApi } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { AllLeasesTable } from '@/components/leases/AllLeasesTable';
import { UploadButton } from '@/components/leases/UploadButton';
import { Loader2, Search, Filter } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

export default function HistoryPage() {
  const { currentOrg } = useAuth();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'completed' | 'processing' | 'failed'>('all');
  const [sortBy, setSortBy] = useState<'updated_at' | 'created_at' | 'filename'>('updated_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const { data: leases, isLoading, error, refetch } = useQuery({
    queryKey: ['leases', currentOrg?.id],
    queryFn: () => leaseApi.list(currentOrg?.id),
    enabled: !!currentOrg,
  });

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="h-12 w-12 animate-spin text-amber-500" />
          <p className="mt-4 text-slate-600 font-medium">Loading leases...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <p className="text-red-800 font-medium">Failed to load leases. Please try again.</p>
        </div>
      </div>
    );
  }

  // Filter and sort leases
  let filteredLeases = leases || [];

  // Apply search filter
  if (search) {
    filteredLeases = filteredLeases.filter((lease) =>
      lease.original_filename.toLowerCase().includes(search.toLowerCase())
    );
  }

  // Apply status filter
  if (statusFilter !== 'all') {
    filteredLeases = filteredLeases.filter((lease) => lease.status === statusFilter);
  }

  // Apply sorting
  filteredLeases = [...filteredLeases].sort((a, b) => {
    let aValue: any;
    let bValue: any;

    if (sortBy === 'filename') {
      aValue = a.original_filename.toLowerCase();
      bValue = b.original_filename.toLowerCase();
    } else {
      aValue = new Date(a[sortBy]).getTime();
      bValue = new Date(b[sortBy]).getTime();
    }

    if (sortOrder === 'asc') {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-3xl font-bold text-slate-900">All Leases</h2>
            <p className="mt-1 text-slate-600">
              Complete history of all uploaded leases
            </p>
          </div>
          <UploadButton onUploadComplete={refetch} />
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6 bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
              <Input
                type="text"
                placeholder="Search leases by filename..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {/* Status Filter */}
          <div className="flex gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as any)}
              className="px-4 py-2 border border-slate-200 rounded-lg text-sm font-medium text-slate-700 bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-amber-500"
            >
              <option value="all">All Status</option>
              <option value="completed">Completed</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
            </select>

            {/* Sort */}
            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [by, order] = e.target.value.split('-');
                setSortBy(by as any);
                setSortOrder(order as any);
              }}
              className="px-4 py-2 border border-slate-200 rounded-lg text-sm font-medium text-slate-700 bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-amber-500"
            >
              <option value="updated_at-desc">Latest Updated</option>
              <option value="updated_at-asc">Oldest Updated</option>
              <option value="created_at-desc">Latest Created</option>
              <option value="created_at-asc">Oldest Created</option>
              <option value="filename-asc">Filename A-Z</option>
              <option value="filename-desc">Filename Z-A</option>
            </select>
          </div>
        </div>

        {/* Results count */}
        <div className="mt-3 text-sm text-slate-500">
          Showing {filteredLeases.length} of {leases?.length || 0} leases
        </div>
      </div>

      {/* Table */}
      {filteredLeases.length > 0 ? (
        <AllLeasesTable leases={filteredLeases} onUpdate={refetch} />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <p className="text-slate-600">No leases found matching your filters.</p>
        </div>
      )}
    </div>
  );
}
