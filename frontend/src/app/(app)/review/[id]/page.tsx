'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { leaseApi, extractionApi, handleApiError } from '@/lib/api';
import { PDFViewer } from '@/components/pdf/PDFViewer';
import { FieldReviewPanel } from '@/components/review/FieldReviewPanel';
import { ExtractionProgress } from '@/components/ui/ExtractionProgress';
import { Loader2, ArrowLeft, FileText } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

interface Citation {
  page: number;
  quote: string;
  bounding_box?: {
    x0: number;
    y0: number;
    x1: number;
    y1: number;
  };
}

interface FieldValue {
  path: string;
  label: string;
  value: any;
  confidence: number;
  reasoning?: string;
  citation?: Citation;
  category: string;
}

interface FieldFeedback {
  fieldPath: string;
  isCorrect: boolean;
  correctedValue?: any;
  notes?: string;
}

export default function ReviewPage() {
  const params = useParams();
  const leaseId = parseInt(params.id as string);

  const [activeField, setActiveField] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<Record<string, FieldFeedback>>({});
  const [pdfUrl, setPdfUrl] = useState<string>('');
  const [showProgress, setShowProgress] = useState(true);

  const { data: lease, isLoading: leaseLoading } = useQuery({
    queryKey: ['lease', leaseId],
    queryFn: () => leaseApi.get(leaseId),
    enabled: !!leaseId,
  });

  const { data: extraction, isLoading: extractionLoading, refetch: refetchExtraction } = useQuery({
    queryKey: ['extraction', leaseId],
    queryFn: async () => {
      const extractions = await extractionApi.getByLease(leaseId);
      if (extractions && extractions.length > 0) {
        // Extraction exists, hide progress
        setShowProgress(false);
        return extractions[0];
      }
      return null;
    },
    enabled: !!leaseId,
    retry: 3,
    retryDelay: 2000, // Retry every 2 seconds
  });

  const { data: schema } = useQuery({
    queryKey: ['schema'],
    queryFn: () => extractionApi.getFieldSchema(),
  });

  useEffect(() => {
    if (lease) {
      setPdfUrl(`${process.env.NEXT_PUBLIC_API_URL}/api/leases/${leaseId}/pdf`);
    }
  }, [lease, leaseId]);

  const handleExtractionComplete = useCallback(() => {
    setShowProgress(false);
    refetchExtraction();
  }, [refetchExtraction]);

  const fieldValues: FieldValue[] = useMemo(() => {
    if (!extraction || !schema) return [];

    const fields: FieldValue[] = [];
    const extractions = extraction.extractions || {};
    const reasoning = extraction.reasoning || {};
    const confidence = extraction.confidence || {};
    const citations = extraction.citations || {};

    for (const field of schema.fields) {
      const citation = citations[field.path];
      fields.push({
        path: field.path,
        label: field.label,
        value: extractions[field.path],
        confidence: confidence[field.path] || 0,
        reasoning: reasoning[field.path],
        citation: citation,
        category: field.category,
      });
    }

    return fields;
  }, [extraction, schema]);

  const heatmapFields = useMemo(() => {
    return fieldValues
      .filter((f) => f.citation?.bounding_box)
      .map((f) => ({
        fieldPath: f.path,
        label: f.label,
        page: f.citation!.page,
        confidence: f.confidence,
        boundingBox: f.citation!.bounding_box,
      }));
  }, [fieldValues]);

  const handleFieldClick = useCallback((fieldPath: string) => {
    setActiveField(fieldPath);
    const field = fieldValues.find((f) => f.path === fieldPath);
    if (field?.citation?.page && typeof window !== 'undefined') {
      // Use scrollToField if bounding box exists, otherwise fall back to scrollToPage
      if (field.citation.bounding_box) {
        (window as any).pdfScrollToField?.(field.citation.page, field.citation.bounding_box);
      } else {
        (window as any).pdfScrollToPage?.(field.citation.page);
      }
    }
  }, [fieldValues]);

  const handleFeedback = useCallback((fieldPath: string, isCorrect: boolean, correctedValue?: any) => {
    setFeedback((prev) => ({
      ...prev,
      [fieldPath]: {
        fieldPath,
        isCorrect,
        correctedValue,
      },
    }));
  }, []);

  const submitFeedbackMutation = useMutation({
    mutationFn: async () => {
      if (!extraction) return;
      
      const promises = Object.values(feedback).map((item) => {
        const field = fieldValues.find((f) => f.path === item.fieldPath);
        if (!field) return null;
        
        return extractionApi.submitCorrection(extraction.id, {
          field_path: item.fieldPath,
          original_value: field.value,
          corrected_value: item.correctedValue || field.value,
          correction_type: item.isCorrect ? 'accept' : item.correctedValue ? 'edit' : 'reject',
          notes: item.notes || '',
        });
      });
      
      await Promise.all(promises.filter(Boolean));
    },
    onSuccess: () => {
      alert('Feedback submitted successfully!');
      setFeedback({});
    },
    onError: (error) => {
      alert(`Failed to submit feedback: ${handleApiError(error)}`);
    },
  });

  // Show extraction progress if we're still extracting
  if (showProgress) {
    return (
      <div className="h-screen flex flex-col bg-slate-50">
        {/* Header */}
        <header className="bg-white border-b border-slate-200 px-4 sm:px-6 py-3 flex items-center justify-between sticky top-16 z-40">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="flex items-center gap-2 text-slate-600 hover:text-slate-900 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              <span className="hidden sm:inline">Back to Dashboard</span>
            </Link>
            <div className="h-6 w-px bg-slate-200 hidden sm:block" />
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-slate-400" />
              <span className="font-medium text-slate-900 truncate max-w-xs">
                {lease?.original_filename || 'Loading...'}
              </span>
            </div>
          </div>
        </header>

        {/* PDF and Progress Side by Side */}
        <div className="flex-1 flex overflow-hidden">
          {/* PDF Preview */}
          <div className="flex-1 bg-slate-100 flex items-center justify-center p-4">
            {pdfUrl ? (
              <PDFViewer
                pdfUrl={pdfUrl}
                activeHighlight={null}
                onPageChange={() => {}}
              />
            ) : (
              <div className="flex flex-col items-center gap-4">
                <Loader2 className="w-12 h-12 animate-spin text-slate-400" />
                <p className="text-slate-600">Loading PDF...</p>
              </div>
            )}
          </div>

          {/* Extraction Progress */}
          <div className="w-1/2 bg-white border-l border-slate-200 flex items-center justify-center p-6">
            <ExtractionProgress
              leaseId={leaseId}
              onComplete={handleExtractionComplete}
            />
          </div>
        </div>
      </div>
    );
  }

  const isLoading = leaseLoading || extractionLoading;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-12 w-12 animate-spin text-amber-500" />
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-4 sm:px-6 py-3 flex items-center justify-between sticky top-16 z-40">
        <div className="flex items-center gap-4">
          <Link
            href="/"
            className="flex items-center gap-2 text-slate-600 hover:text-slate-900 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span className="hidden sm:inline">Back</span>
          </Link>
          <div className="h-6 w-px bg-slate-200 hidden sm:block" />
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <FileText className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-slate-900 truncate max-w-[200px] sm:max-w-md">
                {lease?.original_filename}
              </h1>
              <p className="text-xs text-slate-500">
                Review and verify extracted data
              </p>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 text-sm text-slate-600">
            <span className="font-medium text-slate-900">
              {Object.keys(feedback).length}
            </span>
            <span>/</span>
            <span>{fieldValues.length}</span>
            <span className="text-slate-400">reviewed</span>
          </div>
          <Button
            onClick={() => submitFeedbackMutation.mutate()}
            disabled={Object.keys(feedback).length < fieldValues.length || submitFeedbackMutation.isPending}
            variant="primary"
          >
            {submitFeedbackMutation.isPending ? 'Submitting...' : 'Submit Review'}
          </Button>
        </div>
      </header>

      {/* Main Content - 2 Pane Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Pane - PDF Viewer */}
        <div className="w-1/2 border-r border-slate-200 bg-slate-100">
          <PDFViewer
            url={pdfUrl}
            heatmapFields={heatmapFields}
            activeField={activeField}
            onFieldClick={handleFieldClick}
          />
        </div>

        {/* Right Pane - Field Review */}
        <div className="w-1/2 bg-white">
          <FieldReviewPanel
            fields={fieldValues}
            activeField={activeField}
            feedback={feedback}
            onFieldClick={handleFieldClick}
            onFeedback={handleFeedback}
          />
        </div>
      </div>
    </div>
  );
}
