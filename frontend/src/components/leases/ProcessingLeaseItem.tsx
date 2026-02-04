'use client';

import { Lease } from '@/types';
import { Button } from '@/components/ui/button';
import { formatFileSize, formatDateTime } from '@/lib/utils';
import { FileText, Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface ProcessingLeaseItemProps {
  lease: Lease;
}

export function ProcessingLeaseItem({ lease }: ProcessingLeaseItemProps) {
  const router = useRouter();

  return (
    <div className="px-6 py-4 hover:bg-slate-50 transition-colors">
      <div className="flex items-center justify-between gap-4">
        {/* File Info */}
        <div className="flex items-center gap-4 flex-1 min-w-0">
          <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
            <FileText className="w-6 h-6 text-blue-600" />
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

        {/* Processing Indicator */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-sm text-blue-600">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="font-medium">AI extraction in progress...</span>
          </div>
          <Button
            onClick={() => router.push(`/leases/${lease.id}`)}
            variant="ghost"
            size="sm"
            className="text-slate-600 hover:text-slate-900"
          >
            View Progress
          </Button>
        </div>
      </div>
    </div>
  );
}
