'use client';

import { useQuery } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import { leaseApi, extractionApi } from '@/lib/api';
import { ExtractionReview } from '@/components/extraction/ExtractionReview';
import { Loader2 } from 'lucide-react';

export default function LeaseDetailPage() {
  const params = useParams();
  const leaseId = parseInt(params.id as string);

  const { data: lease, isLoading: leaseLoading } = useQuery({
    queryKey: ['lease', leaseId],
    queryFn: () => leaseApi.get(leaseId),
  });

  const { data: extractions, isLoading: extractionsLoading } = useQuery({
    queryKey: ['extractions', leaseId],
    queryFn: () => extractionApi.getByLease(leaseId),
  });

  const isLoading = leaseLoading || extractionsLoading;
  const latestExtraction = extractions?.[0];

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  if (!lease) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Lease not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">{lease.original_filename}</h2>
        <p className="mt-1 text-sm text-gray-600">
          Status: <span className="font-medium">{lease.status}</span>
        </p>
      </div>

      {latestExtraction ? (
        <ExtractionReview extraction={latestExtraction} lease={lease} />
      ) : (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800">
            No extraction data available. Please extract data from this lease first.
          </p>
        </div>
      )}
    </div>
  );
}
