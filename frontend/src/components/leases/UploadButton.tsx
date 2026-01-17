'use client';

import { useState, useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import { leaseApi, extractionApi, handleApiError } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Upload, Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface UploadButtonProps {
  onUploadComplete?: () => void;
}

export function UploadButton({ onUploadComplete }: UploadButtonProps) {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadProgress, setUploadProgress] = useState<string>('');

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      setUploadProgress('Uploading PDF...');
      const lease = await leaseApi.upload(file);

      setUploadProgress('Extracting data with AI...');
      const extraction = await extractionApi.extract(lease.id);

      return { lease, extraction };
    },
    onSuccess: ({ lease }) => {
      setUploadProgress('');
      onUploadComplete?.();
      // Navigate to the lease detail page
      router.push(`/leases/${lease.id}`);
    },
    onError: (error: any) => {
      setUploadProgress('');
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
      >
        {uploadMutation.isPending ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            {uploadProgress}
          </>
        ) : (
          <>
            <Upload className="mr-2 h-4 w-4" />
            Upload Lease
          </>
        )}
      </Button>
    </>
  );
}
