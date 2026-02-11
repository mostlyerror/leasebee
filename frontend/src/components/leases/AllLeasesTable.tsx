'use client';

import { Lease } from '@/types';
import { Button } from '@/components/ui/button';
import { formatFileSize, formatDateTime } from '@/lib/utils';
import { FileText, Eye, Trash2, CheckCircle2, Clock, AlertCircle, Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useMutation } from '@tanstack/react-query';
import { leaseApi, handleApiError } from '@/lib/api';

interface AllLeasesTableProps {
  leases: Lease[];
  onUpdate: () => void;
}

function getStatusConfig(status: string) {
  switch (status) {
    case 'completed':
      return {
        icon: CheckCircle2,
        color: 'text-green-600',
        bgColor: 'bg-green-50',
        borderColor: 'border-green-200',
        label: 'Completed',
      };
    case 'processing':
      return {
        icon: Loader2,
        color: 'text-blue-600',
        bgColor: 'bg-blue-50',
        borderColor: 'border-blue-200',
        label: 'Processing',
        animate: true,
      };
    case 'failed':
      return {
        icon: AlertCircle,
        color: 'text-red-600',
        bgColor: 'bg-red-50',
        borderColor: 'border-red-200',
        label: 'Failed',
      };
    default:
      return {
        icon: FileText,
        color: 'text-slate-600',
        bgColor: 'bg-slate-50',
        borderColor: 'border-slate-200',
        label: 'Uploaded',
      };
  }
}

export function AllLeasesTable({ leases, onUpdate }: AllLeasesTableProps) {
  const router = useRouter();

  const deleteMutation = useMutation({
    mutationFn: leaseApi.delete,
    onSuccess: () => {
      onUpdate();
    },
    onError: (error: any) => {
      alert(`Delete failed: ${handleApiError(error)}`);
    },
  });

  const handleView = (leaseId: number, status: string) => {
    if (status === 'completed') {
      router.push(`/review/${leaseId}`);
    } else {
      router.push(`/leases/${leaseId}`);
    }
  };

  const handleDelete = (leaseId: number, filename: string) => {
    if (confirm(`Are you sure you want to delete "${filename}"?`)) {
      deleteMutation.mutate(leaseId);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
      <div className="divide-y divide-slate-100">
        {leases.map((lease) => {
          const statusConfig = getStatusConfig(lease.status);
          const StatusIcon = statusConfig.icon;

          return (
            <div
              key={lease.id}
              className="px-6 py-4 hover:bg-slate-50 transition-colors group"
            >
              <div className="flex items-center justify-between gap-4">
                {/* File Info */}
                <div className="flex items-center gap-4 flex-1 min-w-0">
                  <div className={`w-12 h-12 ${statusConfig.bgColor} rounded-xl flex items-center justify-center flex-shrink-0`}>
                    <FileText className={`w-6 h-6 ${statusConfig.color}`} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <h4 className="text-sm font-semibold text-slate-900 truncate">
                      {lease.original_filename}
                    </h4>
                    <div className="mt-1 flex items-center gap-3 text-xs text-slate-500">
                      <span>{formatFileSize(lease.file_size)}</span>
                      {lease.page_count && (
                        <span>• {lease.page_count} pages</span>
                      )}
                      <span>• {formatDateTime(lease.created_at)}</span>
                      {lease.avg_confidence != null && (
                        <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${
                          lease.avg_confidence >= 0.85
                            ? 'bg-green-100 text-green-700'
                            : lease.avg_confidence >= 0.70
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-red-100 text-red-700'
                        }`}>
                          {Math.round(lease.avg_confidence * 100)}% avg
                          {lease.low_confidence_count ? ` • ${lease.low_confidence_count} low` : ''}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Status & Actions */}
                <div className="flex items-center gap-3">
                  <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium ${statusConfig.bgColor} ${statusConfig.color} border ${statusConfig.borderColor}`}>
                    <StatusIcon className={`w-3.5 h-3.5 ${statusConfig.animate ? 'animate-spin' : ''}`} />
                    {statusConfig.label}
                  </span>

                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Button
                      onClick={() => handleView(lease.id, lease.status)}
                      variant="ghost"
                      size="sm"
                      className="text-slate-600 hover:text-slate-900"
                    >
                      <Eye className="w-4 h-4 mr-1.5" />
                      {lease.status === 'completed' ? 'Review' : 'View'}
                    </Button>
                    <Button
                      onClick={() => handleDelete(lease.id, lease.original_filename)}
                      variant="ghost"
                      size="sm"
                      className="text-slate-400 hover:text-red-600"
                      disabled={deleteMutation.isPending}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>

              {lease.error_message && (
                <div className="mt-3 bg-red-50 border border-red-100 rounded-lg p-3">
                  <p className="text-sm text-red-700">{lease.error_message}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
