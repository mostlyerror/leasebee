'use client';

import { Lease } from '@/types';
import { Button } from '@/components/ui/button';
import { formatFileSize, formatDateTime } from '@/lib/utils';
import { FileText, ArrowRight, RefreshCw, Trash2 } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface LeaseQueueItemProps {
  lease: Lease;
  actionType: 'review' | 'retry';
  onDelete?: (leaseId: number) => void;
  onRetry?: (leaseId: number) => void;
}

export function LeaseQueueItem({ lease, actionType, onDelete, onRetry }: LeaseQueueItemProps) {
  const router = useRouter();

  const handlePrimaryAction = () => {
    if (actionType === 'review') {
      router.push(`/review/${lease.id}`);
    } else if (actionType === 'retry' && onRetry) {
      onRetry(lease.id);
    }
  };

  return (
    <div className="px-6 py-4 hover:bg-slate-50 transition-colors">
      <div className="flex items-center justify-between gap-4">
        {/* File Info */}
        <div className="flex items-center gap-4 flex-1 min-w-0">
          <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center flex-shrink-0">
            <FileText className="w-6 h-6 text-slate-600" />
          </div>
          <div className="min-w-0 flex-1">
            <h4 className="text-sm font-semibold text-slate-900 truncate">
              {lease.original_filename}
            </h4>
            <div className="mt-1 flex items-center gap-3 text-xs text-slate-500">
              <span>{formatFileSize(lease.file_size)}</span>
              {lease.page_count && <span>• {lease.page_count} pages</span>}
              <span>• {formatDateTime(lease.created_at)}</span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          {actionType === 'review' && (
            <Button
              onClick={handlePrimaryAction}
              className="bg-amber-500 hover:bg-amber-600 text-white"
              size="sm"
            >
              Review Now
              <ArrowRight className="w-4 h-4 ml-1.5" />
            </Button>
          )}
          {actionType === 'retry' && (
            <>
              <Button
                onClick={handlePrimaryAction}
                variant="outline"
                size="sm"
                className="text-slate-700 hover:text-slate-900"
              >
                <RefreshCw className="w-4 h-4 mr-1.5" />
                Retry
              </Button>
              {onDelete && (
                <Button
                  onClick={() => onDelete(lease.id)}
                  variant="ghost"
                  size="sm"
                  className="text-slate-400 hover:text-red-600"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
