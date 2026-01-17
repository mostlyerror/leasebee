'use client';

import { Lease } from '@/types';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { formatFileSize, formatDateTime, getStatusColor } from '@/lib/utils';
import { FileText, Eye, Trash2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useMutation } from '@tanstack/react-query';
import { leaseApi, handleApiError } from '@/lib/api';

interface LeaseListProps {
  leases: Lease[];
  onUpdate: () => void;
}

export function LeaseList({ leases, onUpdate }: LeaseListProps) {
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

  const handleView = (leaseId: number) => {
    router.push(`/leases/${leaseId}`);
  };

  const handleDelete = (leaseId: number, filename: string) => {
    if (confirm(`Are you sure you want to delete "${filename}"?`)) {
      deleteMutation.mutate(leaseId);
    }
  };

  return (
    <div className="space-y-4">
      {leases.map((lease) => (
        <Card key={lease.id}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4 flex-1">
                <div className="bg-blue-100 p-3 rounded-lg">
                  <FileText className="h-6 w-6 text-blue-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg font-medium text-gray-900 truncate">
                    {lease.original_filename}
                  </h3>
                  <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                    <span>{formatFileSize(lease.file_size)}</span>
                    {lease.page_count && (
                      <span>{lease.page_count} pages</span>
                    )}
                    <span>{formatDateTime(lease.created_at)}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-3 ml-4">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(
                    lease.status
                  )}`}
                >
                  {lease.status}
                </span>
                <Button
                  onClick={() => handleView(lease.id)}
                  variant="outline"
                  size="sm"
                >
                  <Eye className="h-4 w-4 mr-1" />
                  View
                </Button>
                <Button
                  onClick={() => handleDelete(lease.id, lease.original_filename)}
                  variant="destructive"
                  size="sm"
                  disabled={deleteMutation.isPending}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
            {lease.error_message && (
              <div className="mt-4 bg-red-50 border border-red-200 rounded-md p-3">
                <p className="text-sm text-red-800">{lease.error_message}</p>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
