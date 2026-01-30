'use client';

import { useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { leaseApi } from '@/lib/api';
import { LeaseList } from '@/components/leases/LeaseList';
import { UploadButton } from '@/components/leases/UploadButton';
import { EmptyState } from '@/components/leases/EmptyState';
import { Loader2 } from 'lucide-react';

export default function HomePage() {
  const { data: leases, isLoading, error, refetch } = useQuery({
    queryKey: ['leases'],
    queryFn: leaseApi.list,
  });

  // Ref to trigger upload button from empty state
  const uploadButtonRef = useRef<{ triggerUpload: () => void }>(null);

  const handleEmptyStateUpload = () => {
    // Programmatically click the upload button
    const uploadInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    uploadInput?.click();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">🐝 Lease Dashboard</h2>
            <p className="mt-1 text-sm text-gray-600">
              Upload and manage your commercial lease documents - sweet extraction, no sting!
            </p>
          </div>
          <UploadButton onUploadComplete={refetch} />
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center items-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Failed to load leases. Please try again.</p>
        </div>
      ) : leases && leases.length > 0 ? (
        <LeaseList leases={leases} onUpdate={refetch} />
      ) : (
        <EmptyState onUploadClick={handleEmptyStateUpload} />
      )}
    </div>
  );
}
