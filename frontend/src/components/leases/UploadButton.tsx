'use client';

import { useState, useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import { leaseApi, extractionApi, handleApiError } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Upload, Loader2, FileUp } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { ExtractionProgress } from '@/components/ui/ExtractionProgress';

interface UploadButtonProps {
  onUploadComplete?: () => void;
}

export function UploadButton({ onUploadComplete }: UploadButtonProps) {
  const router = useRouter();
  const { currentOrg } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadStage, setUploadStage] = useState<'idle' | 'uploading' | 'extracting' | 'complete'>('idle');
  const [currentLeaseId, setCurrentLeaseId] = useState<number | null>(null);

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      if (!currentOrg) {
        throw new Error('Please select an organization first');
      }

      setUploadStage('uploading');
      const lease = await leaseApi.upload(file, currentOrg.id);
      setCurrentLeaseId(lease.id);

      // Trigger extraction (fire and forget - extraction runs async on backend)
      // We don't await to avoid blocking the redirect
      fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/extractions/extract/${lease.id}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('leasebee_access_token')}`,
        },
      }).catch(err => {
        console.error('Extraction failed:', err);
      });

      return lease;
    },
    onSuccess: (lease) => {
      onUploadComplete?.();

      // Redirect immediately to review page where we'll show progress
      router.push(`/review/${lease.id}`);

      // Reset state after navigation
      setTimeout(() => {
        setUploadStage('idle');
        setCurrentLeaseId(null);
      }, 500);
    },
    onError: (error: any) => {
      setUploadStage('idle');
      setCurrentLeaseId(null);
      alert(`Upload failed: ${handleApiError(error)}`);
    },
  });

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (file.type !== 'application/pdf') {
        alert('Please select a PDF file');
        return;
      }
      uploadMutation.mutate(file);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };


  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept="application/pdf"
        onChange={handleFileSelect}
        className="hidden"
      />
      <Button
        onClick={handleClick}
        disabled={uploadMutation.isPending}
        size="lg"
        className="bg-amber-500 hover:bg-amber-600 text-white h-11 px-6"
      >
        {uploadMutation.isPending ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            {uploadStage === 'uploading' ? 'Uploading...' : 'Processing...'}
          </>
        ) : (
          <>
            <FileUp className="mr-2 h-4 w-4" />
            Upload Lease
          </>
        )}
      </Button>
    </>
  );
}
