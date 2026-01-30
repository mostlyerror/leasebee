'use client';

import { useState, useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import { leaseApi, extractionApi, handleApiError } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Upload, Loader2, FileUp } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { ExtractionProgress } from '@/components/ui/ExtractionProgress';

interface UploadButtonProps {
  onUploadComplete?: () => void;
}

export function UploadButton({ onUploadComplete }: UploadButtonProps) {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadStage, setUploadStage] = useState<'idle' | 'uploading' | 'extracting' | 'complete'>('idle');
  const [currentLeaseId, setCurrentLeaseId] = useState<number | null>(null);

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      setUploadStage('uploading');
      const lease = await leaseApi.upload(file);
      setCurrentLeaseId(lease.id);

      setUploadStage('extracting');
      const extraction = await extractionApi.extract(lease.id);

      return { lease, extraction };
    },
    onSuccess: ({ lease }) => {
      setUploadStage('complete');
      onUploadComplete?.();
      setTimeout(() => {
        router.push(`/review/${lease.id}`);
        setTimeout(() => {
          setUploadStage('idle');
          setCurrentLeaseId(null);
        }, 500);
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

  const handleProgressComplete = () => {
    if (currentLeaseId) {
      router.push(`/review/${currentLeaseId}`);
      setTimeout(() => {
        setUploadStage('idle');
        setCurrentLeaseId(null);
      }, 500);
    }
  };

  if (uploadStage === 'extracting' && currentLeaseId) {
    return (
      <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div className="w-full max-w-2xl">
          <ExtractionProgress 
            leaseId={currentLeaseId} 
            onComplete={handleProgressComplete}
          />
        </div>
      </div>
    );
  }

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
