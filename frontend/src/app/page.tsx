'use client';

import { useQuery } from '@tanstack/react-query';
import { leaseApi } from '@/lib/api';
import { LeaseList } from '@/components/leases/LeaseList';
import { UploadButton } from '@/components/leases/UploadButton';
import { Loader2 } from 'lucide-react';

export default function HomePage() {
  const { data: leases, isLoading, error, refetch } = useQuery({
    queryKey: ['leases'],
    queryFn: leaseApi.list,
  });

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
        <div className="text-center py-12 bg-white rounded-lg border-2 border-dashed border-gray-300">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No leases</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by uploading a commercial lease PDF.
          </p>
          <div className="mt-6">
            <UploadButton onUploadComplete={refetch} />
          </div>
        </div>
      )}
    </div>
  );
}
