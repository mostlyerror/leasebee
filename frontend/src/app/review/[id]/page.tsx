'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { leaseApi, extractionApi, handleApiError } from '@/lib/api';
import { PDFViewer } from '@/components/pdf/PDFViewer';
import { FieldReviewPanel } from '@/components/review/FieldReviewPanel';
import { Loader2, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

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

  // Fetch lease details
  const { data: lease, isLoading: leaseLoading } = useQuery({
    queryKey: ['lease', leaseId],
    queryFn: () => leaseApi.get(leaseId),
    enabled: !!leaseId,
  });

  // Fetch extraction
  const { data: extraction, isLoading: extractionLoading } = useQuery({
    queryKey: ['extraction', leaseId],
    queryFn: async () => {
      const extractions = await extractionApi.getByLease(leaseId);
      return extractions[0]; // Get the most recent extraction
    },
    enabled: !!leaseId,
  });

  // Fetch field schema
  const { data: schema } = useQuery({
    queryKey: ['schema'],
    queryFn: () => extractionApi.getFieldSchema(),
  });

  // Get PDF URL
  useEffect(() => {
    if (lease) {
      // Use the direct PDF endpoint that streams the file
      setPdfUrl(`${process.env.NEXT_PUBLIC_API_URL}/api/leases/${leaseId}/pdf`);
    }
  }, [lease, leaseId]);

  // Build field values from extraction
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

  // Build highlights for PDF
  const highlights = useMemo(() => {
    return fieldValues
      .filter((f) => f.citation?.bounding_box)
      .map((f) => ({
        fieldPath: f.path,
        page: f.citation!.page,
        boundingBox: f.citation!.bounding_box,
        color: 'yellow',
      }));
  }, [fieldValues]);

  // Handle field click - scroll to citation
  const handleFieldClick = useCallback((fieldPath: string) => {
    setActiveField(fieldPath);
    
    const field = fieldValues.find((f) => f.path === fieldPath);
    if (field?.citation?.page && typeof window !== 'undefined') {
      // Scroll to page
      (window as any).pdfScrollToPage?.(field.citation.page);
    }
  }, [fieldValues]);

  // Handle feedback
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

  // Submit feedback mutation
  const submitFeedbackMutation = useMutation({
    mutationFn: async () => {
      if (!extraction) return;
      
      // Submit each feedback item as a correction
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
      // Reset feedback after successful submission
      setFeedback({});
    },
    onError: (error) => {
      alert(`Failed to submit feedback: ${handleApiError(error)}`);
    },
  });

  const isLoading = leaseLoading || extractionLoading;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white border-b px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            href="/"
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="w-5 h-5" />
            Back
          </Link>
          <div>
            <h1 className="text-lg font-semibold text-gray-900">
              Review: {lease?.original_filename}
            </h1>
            <p className="text-sm text-gray-600">
              AI extraction review with source verification
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600">
            {Object.keys(feedback).length} / {fieldValues.length} reviewed
          </span>
          <button
            onClick={() => submitFeedbackMutation.mutate()}
            disabled={Object.keys(feedback).length < fieldValues.length}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 disabled:opacity-50"
          >
            Submit Review
          </button>
        </div>
      </header>

      {/* Main Content - 2 Pane Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Pane - PDF Viewer */}
        <div className="w-1/2 border-r">
          <PDFViewer
            url={pdfUrl}
            highlights={highlights}
            activeField={activeField}
          />
        </div>

        {/* Right Pane - Field Review */}
        <div className="w-1/2">
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
