'use client';

import { useState, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Extraction, Lease, FieldDefinition } from '@/types';
import { extractionApi, handleApiError } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FieldEditor } from './FieldEditor';
import { Save, Download, Loader2 } from 'lucide-react';
import { downloadJSON } from '@/lib/utils';

interface ExtractionReviewProps {
  extraction: Extraction;
  lease: Lease;
}

export function ExtractionReview({ extraction, lease }: ExtractionReviewProps) {
  const [editedData, setEditedData] = useState(extraction.extractions);
  const [hasChanges, setHasChanges] = useState(false);

  // Load field schema
  const { data: fieldSchema } = useQuery({
    queryKey: ['fieldSchema'],
    queryFn: extractionApi.getFieldSchema,
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data: Record<string, any>) =>
      extractionApi.update(extraction.id, data),
    onSuccess: () => {
      setHasChanges(false);
      alert('Changes saved successfully!');
    },
    onError: (error: any) => {
      alert(`Save failed: ${handleApiError(error)}`);
    },
  });

  // Export mutation
  const exportMutation = useMutation({
    mutationFn: () =>
      extractionApi.export(extraction.id, {
        include_citations: false,
        include_reasoning: false,
      }),
    onSuccess: (data) => {
      const filename = `${lease.original_filename.replace('.pdf', '')}_extracted.json`;
      downloadJSON(data.data, filename);
    },
    onError: (error: any) => {
      alert(`Export failed: ${handleApiError(error)}`);
    },
  });

  const handleFieldChange = (fieldPath: string, value: any) => {
    setEditedData((prev) => ({
      ...prev,
      [fieldPath]: value,
    }));
    setHasChanges(true);
  };

  const handleSave = () => {
    updateMutation.mutate(editedData);
  };

  const handleExport = () => {
    exportMutation.mutate();
  };

  // Group fields by category
  const fieldsByCategory = fieldSchema?.fields.reduce((acc, field) => {
    if (!acc[field.category]) {
      acc[field.category] = [];
    }
    acc[field.category].push(field);
    return acc;
  }, {} as Record<string, FieldDefinition[]>) || {};

  const categories = Object.keys(fieldsByCategory);

  return (
    <div className="space-y-6">
      {/* Action Bar */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                <span className="font-medium">Model:</span> {extraction.model_version}
              </div>
              {extraction.total_cost && (
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Cost:</span> ${extraction.total_cost.toFixed(4)}
                </div>
              )}
              {extraction.processing_time_seconds && (
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Time:</span> {extraction.processing_time_seconds.toFixed(1)}s
                </div>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <Button
                onClick={handleExport}
                variant="outline"
                disabled={exportMutation.isPending}
              >
                {exportMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Download className="mr-2 h-4 w-4" />
                )}
                Export JSON
              </Button>
              <Button
                onClick={handleSave}
                disabled={!hasChanges || updateMutation.isPending}
              >
                {updateMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Save className="mr-2 h-4 w-4" />
                )}
                Save Changes
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Field Editor by Category */}
      {categories.length === 0 ? (
        <div className="flex justify-center items-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      ) : (
        <div className="space-y-6">
          {categories.map((category) => (
            <Card key={category}>
              <CardHeader>
                <CardTitle className="text-lg capitalize">
                  {category.replace(/_/g, ' ')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {fieldsByCategory[category].map((field) => {
                    const value = editedData[field.path];
                    const confidence = extraction.confidence?.[field.path];
                    const reasoning = extraction.reasoning?.[field.path];
                    const citation = extraction.citations?.[field.path];

                    return (
                      <FieldEditor
                        key={field.path}
                        field={field}
                        value={value}
                        confidence={confidence}
                        reasoning={reasoning}
                        citation={citation}
                        onChange={(newValue) => handleFieldChange(field.path, newValue)}
                      />
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Save reminder */}
      {hasChanges && (
        <div className="fixed bottom-6 right-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4 shadow-lg">
          <p className="text-sm text-yellow-800 font-medium">
            You have unsaved changes
          </p>
        </div>
      )}
    </div>
  );
}
