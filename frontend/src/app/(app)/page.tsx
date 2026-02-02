'use client';

import { useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { leaseApi } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { LeaseList } from '@/components/leases/LeaseList';
import { UploadButton } from '@/components/leases/UploadButton';
import { EmptyState } from '@/components/leases/EmptyState';
import { StatsCards } from '@/components/leases/StatsCards';
import { CreateOrganizationModal } from '@/components/organizations/CreateOrganizationModal';
import { Loader2, FileText, Clock, CheckCircle2 } from 'lucide-react';

export default function HomePage() {
  const { currentOrg, refetchUser } = useAuth();
  const [showCreateOrgModal, setShowCreateOrgModal] = useState(false);

  const { data: leases, isLoading, error, refetch } = useQuery({
    queryKey: ['leases', currentOrg?.id],
    queryFn: () => leaseApi.list(currentOrg?.id),
    enabled: !!currentOrg,
  });

  const handleEmptyStateUpload = () => {
    const uploadInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    uploadInput?.click();
  };

  // Calculate stats
  const totalLeases = leases?.length || 0;
  const processedLeases = leases?.filter(l => l.status === 'completed').length || 0;
  const timeSaved = processedLeases * 120; // 2 hours saved per lease (120 minutes)

  if (!currentOrg) {
    return (
      <>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-slate-900 mb-2">No Organization Yet</h2>
            <p className="text-slate-600 mb-6 max-w-md">
              You need to create or join an organization to start managing leases.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowCreateOrgModal(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent text-base font-medium rounded-lg text-white bg-amber-500 hover:bg-amber-600 transition-colors"
              >
                Create Organization
              </button>
            </div>
          </div>
        </div>

        <CreateOrganizationModal
          isOpen={showCreateOrgModal}
          onClose={() => setShowCreateOrgModal(false)}
          onSuccess={refetchUser}
        />
      </>
    );
  }

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="h-12 w-12 animate-spin text-amber-500" />
          <p className="mt-4 text-slate-600 font-medium">Loading your leases...</p>
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

  const hasLeases = leases && leases.length > 0;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header Section */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-3xl font-bold text-slate-900">Dashboard</h2>
            <p className="mt-1 text-slate-600">
              Manage and review your commercial lease extractions
            </p>
          </div>
          <UploadButton onUploadComplete={refetch} />
        </div>
      </div>

      {/* Stats Cards - Only show if has leases */}
      {hasLeases && (
        <StatsCards 
          totalLeases={totalLeases}
          processedLeases={processedLeases}
          timeSaved={timeSaved}
        />
      )}

      {/* Content */}
      {hasLeases ? (
        <div className="mt-8">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                <FileText className="w-5 h-5 text-slate-400" />
                Your Leases
              </h3>
              <span className="text-sm text-slate-500">
                {leases.length} document{leases.length !== 1 ? 's' : ''}
              </span>
            </div>
            <LeaseList leases={leases} onUpdate={refetch} />
          </div>
        </div>
      ) : (
        <EmptyState onUploadClick={handleEmptyStateUpload} />
      )}
    </div>
  );
}
