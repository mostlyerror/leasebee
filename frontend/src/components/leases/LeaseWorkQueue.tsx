'use client';

import { useState } from 'react';
import { Lease } from '@/types';
import { LeaseSection } from './LeaseSection';
import { LeaseQueueItem } from './LeaseQueueItem';
import { ProcessingLeaseItem } from './ProcessingLeaseItem';
import { AlertCircle, Clock, AlertTriangle } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { leaseApi, handleApiError, extractionApi } from '@/lib/api';

interface LeaseWorkQueueProps {
  leases: Lease[];
  onUpdate: () => void;
}

export function LeaseWorkQueue({ leases, onUpdate }: LeaseWorkQueueProps) {
  const [confidenceFilter, setConfidenceFilter] = useState<number | null>(null);

  const deleteMutation = useMutation({
    mutationFn: leaseApi.delete,
    onSuccess: onUpdate,
    onError: (error: any) => {
      alert(`Delete failed: ${handleApiError(error)}`);
    },
  });

  const retryMutation = useMutation({
    mutationFn: extractionApi.extract,
    onSuccess: onUpdate,
    onError: (error: any) => {
      alert(`Retry failed: ${handleApiError(error)}`);
    },
  });

  // Group leases by status
  const needsReview = leases
    .filter((l) => l.status === 'completed')
    .filter((l) => confidenceFilter === null || (l.avg_confidence != null && l.avg_confidence <= confidenceFilter))
    // Sort by avg_confidence ascending (lowest confidence first = most needs review)
    .sort((a, b) => (a.avg_confidence ?? 1) - (b.avg_confidence ?? 1));
  const processing = leases.filter((l) => l.status === 'processing');
  const failed = leases.filter((l) => l.status === 'failed');

  const handleDelete = (leaseId: number) => {
    const lease = leases.find((l) => l.id === leaseId);
    if (lease && confirm(`Are you sure you want to delete "${lease.original_filename}"?`)) {
      deleteMutation.mutate(leaseId);
    }
  };

  const handleRetry = (leaseId: number) => {
    retryMutation.mutate(leaseId);
  };

  return (
    <div className="space-y-4">
      {/* Needs Review Section */}
      {(needsReview.length > 0 || confidenceFilter !== null) && (
        <LeaseSection
          title="NEEDS REVIEW"
          count={needsReview.length}
          icon={<AlertCircle className="w-6 h-6" />}
          color="blue"
          defaultExpanded={true}
          headerExtra={
            <select
              value={confidenceFilter ?? ''}
              onChange={(e) => setConfidenceFilter(e.target.value ? parseFloat(e.target.value) : null)}
              onClick={(e) => e.stopPropagation()}
              className="ml-3 px-2 py-1 text-xs border border-slate-200 rounded-md bg-white text-slate-600"
            >
              <option value="">All confidence</option>
              <option value="0.5">Low (&le; 50%)</option>
              <option value="0.7">Medium (&le; 70%)</option>
              <option value="0.85">Below high (&le; 85%)</option>
            </select>
          }
        >
          {needsReview.map((lease) => (
            <LeaseQueueItem
              key={lease.id}
              lease={lease}
              actionType="review"
            />
          ))}
        </LeaseSection>
      )}

      {/* Processing Section */}
      {processing.length > 0 && (
        <LeaseSection
          title="PROCESSING"
          count={processing.length}
          icon={<Clock className="w-6 h-6" />}
          color="amber"
          defaultExpanded={true}
        >
          {processing.map((lease) => (
            <ProcessingLeaseItem key={lease.id} lease={lease} />
          ))}
        </LeaseSection>
      )}

      {/* Failed Section */}
      {failed.length > 0 && (
        <LeaseSection
          title="FAILED"
          count={failed.length}
          icon={<AlertTriangle className="w-6 h-6" />}
          color="red"
          defaultExpanded={true}
        >
          {failed.map((lease) => (
            <LeaseQueueItem
              key={lease.id}
              lease={lease}
              actionType="retry"
              onDelete={handleDelete}
              onRetry={handleRetry}
            />
          ))}
        </LeaseSection>
      )}
    </div>
  );
}
