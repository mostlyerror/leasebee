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
  variant?: 'default' | 'hero';
}

export function UploadButton({ onUploadComplete, variant = 'default' }: UploadButtonProps) {
  const router = useRouter();
  const { currentOrg } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadStage, setUploadStage] = useState<'idle' | 'uploading' | 'extracting' | 'complete'>('idle');
  const [currentLeaseId, setCurrentLeaseId] = useState<number | null>(null);

  const extractMutation = useMutation({
    mutationFn: async (leaseId: number) => {
      return extractionApi.extract(leaseId);
    },
    onError: (error) => {
      alert(`Failed to start extraction: ${handleApiError(error)}`);
    },
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      if (!currentOrg) {
        throw new Error('Please select an organization first');
      }

      setUploadStage('uploading');
      const lease = await leaseApi.upload(file, currentOrg.id);
      setCurrentLeaseId(lease.id);

      return lease;
    },
    onSuccess: (lease) => {
      // Start extraction with proper error handling
      extractMutation.mutate(lease.id);

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


  const buttonClasses = variant === 'hero'
    ? 'bg-amber-500 hover:bg-amber-600 text-white h-14 px-10 text-lg font-bold shadow-lg hover:shadow-xl transition-all hover:scale-105'
    : 'bg-amber-500 hover:bg-amber-600 text-white h-11 px-6';

  const iconSize = variant === 'hero' ? 'h-6 w-6' : 'h-4 w-4';

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
        className={buttonClasses}
      >
        {uploadMutation.isPending ? (
          <>
            <Loader2 className={`mr-2 ${iconSize} animate-spin`} />
            {uploadStage === 'uploading' ? 'Uploading...' : 'Processing...'}
          </>
        ) : (
          <>
            <Upload className={`mr-2 ${iconSize}`} />
            Upload Lease PDF
          </>
        )}
      </Button>
    </>
  );
}
