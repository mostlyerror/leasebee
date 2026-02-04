'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { leaseApi } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { LeaseWorkQueue } from '@/components/leases/LeaseWorkQueue';
import { UploadButton } from '@/components/leases/UploadButton';
import { EmptyState } from '@/components/leases/EmptyState';
import { CreateOrganizationModal } from '@/components/organizations/CreateOrganizationModal';
import { Loader2 } from 'lucide-react';

export default function HomePage() {
  const { currentOrg, refetchUser } = useAuth();
  const [showCreateOrgModal, setShowCreateOrgModal] = useState(false);

  const { data: leases, isLoading, error, refetch } = useQuery({
    queryKey: ['leases', currentOrg?.id],
    queryFn: () => leaseApi.list(currentOrg?.id),
    enabled: !!currentOrg,
    refetchInterval: 10000, // Poll every 10 seconds for processing updates
  });

  const handleEmptyStateUpload = () => {
    const uploadInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    uploadInput?.click();
  };

  // No organization - show create org prompt
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

  // Loading state
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

  // Error state
  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <p className="text-red-800 font-medium">Failed to load leases. Please try again.</p>
        </div>
      </div>
    );
  }

  // Filter for active work only (needs review, processing, failed)
  const activeLeases = leases?.filter(
    (l) => l.status === 'completed' || l.status === 'processing' || l.status === 'failed'
  ) || [];

  const hasActiveWork = activeLeases.length > 0;
  const hasAnyLeases = leases && leases.length > 0;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Empty State - Show full hero */}
      {!hasActiveWork && (
        <EmptyState
          onUploadClick={handleEmptyStateUpload}
          variant={hasAnyLeases ? 'all-caught-up' : 'first-time'}
        />
      )}

      {/* When there's active work, show prominent upload CTA + queue */}
      {hasActiveWork && (
        <>
          {/* Prominent Upload CTA Section */}
          <div className="mb-8">
            <div className="bg-white border-2 border-slate-200 rounded-2xl p-8 sm:p-10 shadow-sm">
              <div className="max-w-4xl mx-auto text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-slate-100 rounded-2xl mb-4">
                  <svg className="w-8 h-8 text-slate-700" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"/>
                    <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd"/>
                  </svg>
                </div>
                <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 mb-3">
                  Ready to Extract Another Lease?
                </h2>
                <p className="text-lg text-slate-600 mb-6 max-w-2xl mx-auto">
                  Upload a commercial lease PDF and get AI-powered extraction in under 2 minutes
                </p>
                <UploadButton
                  onUploadComplete={refetch}
                  variant="hero"
                />
              </div>
            </div>
          </div>

          {/* Active Work Queue */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-xl font-bold text-slate-900">Active Leases</h3>
                <p className="text-sm text-slate-600 mt-1">
                  {activeLeases.length} {activeLeases.length === 1 ? 'lease' : 'leases'} need your attention
                </p>
              </div>
            </div>
          </div>

          <LeaseWorkQueue leases={activeLeases} onUpdate={refetch} />
        </>
      )}
    </div>
  );
}
