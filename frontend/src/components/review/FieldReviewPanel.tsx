'use client';

import { useState } from 'react';
import { Check, X, ChevronDown, ChevronUp, AlertCircle, Quote, FileText } from 'lucide-react';

interface FieldValue {
  path: string;
  label: string;
  value: any;
  confidence: number;
  reasoning?: string;
  citation?: {
    page: number;
    quote: string;
    bounding_box?: { x0: number; y0: number; x1: number; y1: number };
  };
  category: string;
}

interface FieldFeedback {
  fieldPath: string;
  isCorrect: boolean;
  correctedValue?: any;
  notes?: string;
}

interface FieldReviewPanelProps {
  fields: FieldValue[];
  activeField: string | null;
  feedback: Record<string, FieldFeedback>;
  onFieldClick: (fieldPath: string) => void;
  onFeedback: (fieldPath: string, isCorrect: boolean, correctedValue?: any) => void;
}

function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.9) return 'bg-green-100 text-green-800 border-green-200';
  if (confidence >= 0.7) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
  return 'bg-red-100 text-red-800 border-red-200';
}

function getConfidenceLabel(confidence: number): string {
  if (confidence >= 0.9) return 'High';
  if (confidence >= 0.7) return 'Medium';
  return 'Low';
}

export function FieldReviewPanel({
  fields,
  activeField,
  feedback,
  onFieldClick,
  onFeedback,
}: FieldReviewPanelProps) {
  const [expandedField, setExpandedField] = useState<string | null>(null);
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>('');

  // Group fields by category
  const groupedFields = fields.reduce((acc, field) => {
    if (!acc[field.category]) acc[field.category] = [];
    acc[field.category].push(field);
    return acc;
  }, {} as Record<string, FieldValue[]>);

  const handleExpand = (fieldPath: string) => {
    setExpandedField(expandedField === fieldPath ? null : fieldPath);
  };

  const handleFieldClick = (field: FieldValue) => {
    onFieldClick(field.path);
    setExpandedField(field.path);
  };

  const handleStartEdit = (field: FieldValue) => {
    setEditingField(field.path);
    setEditValue(field.value?.toString() || '');
  };

  const handleSaveEdit = (fieldPath: string) => {
    onFeedback(fieldPath, false, editValue);
    setEditingField(null);
  };

  const handleAccept = (fieldPath: string) => {
    onFeedback(fieldPath, true);
  };

  const handleReject = (fieldPath: string) => {
    onFeedback(fieldPath, false);
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="px-4 py-3 border-b bg-gray-50">
        <h2 className="text-lg font-semibold text-gray-900">Extracted Fields</h2>
        <p className="text-sm text-gray-600">
          {fields.length} fields • Review and verify each extraction
        </p>
      </div>

      {/* Field List */}
      <div className="flex-1 overflow-auto">
        {Object.entries(groupedFields).map(([category, categoryFields]) => (
          <div key={category} className="border-b">
            <div className="px-4 py-2 bg-gray-100 text-sm font-medium text-gray-700 uppercase tracking-wide">
              {category.replace(/_/g, ' ')}
            </div>
            <div className="divide-y">
              {categoryFields.map((field) => {
                const isExpanded = expandedField === field.path;
                const isActive = activeField === field.path;
                const fieldFeedback = feedback[field.path];
                const isAccepted = fieldFeedback?.isCorrect === true;
                const isRejected = fieldFeedback?.isCorrect === false;
                const isEditing = editingField === field.path;

                return (
                  <div
                    key={field.path}
                    className={`transition-colors ${
                      isActive ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
                    } ${isAccepted ? 'bg-green-50' : ''} ${isRejected ? 'bg-red-50' : ''}`}
                  >
                    {/* Field Header */}
                    <div
                      className="px-4 py-3 cursor-pointer hover:bg-gray-50"
                      onClick={() => handleFieldClick(field)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-gray-900">
                              {field.label}
                            </span>
                            <span
                              className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getConfidenceColor(
                                field.confidence
                              )}`}
                            >
                              {getConfidenceLabel(field.confidence)} ({Math.round(
                                field.confidence * 100
                              )}%)
                            </span>
                            {isAccepted && (
                              <span className="text-green-600">
                                <Check className="w-4 h-4" />
                              </span>
                            )}
                            {isRejected && (
                              <span className="text-red-600">
                                <X className="w-4 h-4" />
                              </span>
                            )}
                          </div>
                          
                          {/* Field Value */}
                          {isEditing ? (
                            <div className="mt-2 flex gap-2">
                              <input
                                type="text"
                                value={editValue}
                                onChange={(e) => setEditValue(e.target.value)}
                                className="flex-1 px-2 py-1 text-sm border rounded focus:ring-2 focus:ring-blue-500"
                                onClick={(e) => e.stopPropagation()}
                              />
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleSaveEdit(field.path);
                                }}
                                className="px-2 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                              >
                                Save
                              </button>
                            </div>
                          ) : (
                            <div className="mt-1 text-sm text-gray-700">
                              {field.value === null || field.value === undefined ? (
                                <span className="text-gray-400 italic">Not found</span>
                              ) : (
                                <span className="font-medium">{String(field.value)}</span>
                              )}
                            </div>
                          )}
                        </div>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleExpand(field.path);
                          }}
                          className="ml-2 text-gray-400 hover:text-gray-600"
                        >
                          {isExpanded ? (
                            <ChevronUp className="w-5 h-5" />
                          ) : (
                            <ChevronDown className="w-5 h-5" />
                          )}
                        </button>
                      </div>
                    </div>

                    {/* Expanded Details */}
                    {isExpanded && (
                      <div className="px-4 pb-4 border-t bg-gray-50">
                        {/* Reasoning */}
                        {field.reasoning && (
                          <div className="mt-3">
                            <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                              <FileText className="w-4 h-4" />
                              AI Reasoning
                            </div>
                            <p className="mt-1 text-sm text-gray-600 bg-white p-2 rounded border">
                              {field.reasoning}
                            </p>
                          </div>
                        )}

                        {/* Citation */}
                        {field.citation && (
                          <div className="mt-3">
                            <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                              <Quote className="w-4 h-4" />
                              Source (Page {field.citation.page})
                            </div>
                            <blockquote className="mt-1 text-sm text-gray-600 bg-white p-2 rounded border italic">
                              "{field.citation.quote}"
                            </blockquote>
                          </div>
                        )}

                        {/* Action Buttons */}
                        <div className="mt-4 flex gap-2">
                          <button
                            onClick={() => handleAccept(field.path)}
                            className={`flex items-center gap-1 px-3 py-1.5 text-sm font-medium rounded ${
                              isAccepted
                                ? 'bg-green-600 text-white'
                                : 'bg-white border border-gray-300 text-gray-700 hover:bg-green-50'
                            }`}
                          >
                            <Check className="w-4 h-4" />
                            Accept
                          </button>
                          <button
                            onClick={() => handleReject(field.path)}
                            className={`flex items-center gap-1 px-3 py-1.5 text-sm font-medium rounded ${
                              isRejected
                                ? 'bg-red-600 text-white'
                                : 'bg-white border border-gray-300 text-gray-700 hover:bg-red-50'
                            }`}
                          >
                            <X className="w-4 h-4" />
                            Reject
                          </button>
                          <button
                            onClick={() => handleStartEdit(field)}
                            className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium rounded bg-white border border-gray-300 text-gray-700 hover:bg-blue-50"
                          >
                            <AlertCircle className="w-4 h-4" />
                            Edit
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Summary Footer */}
      <div className="px-4 py-3 border-t bg-gray-50">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">
            Accepted: {Object.values(feedback).filter((f) => f.isCorrect).length} / {fields.length}
          </span>
          <span className="text-gray-600">
            Rejected: {Object.values(feedback).filter((f) => !f.isCorrect).length}
          </span>
        </div>
        <button
          className="mt-2 w-full px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={Object.keys(feedback).length < fields.length}
        >
          Submit Review
        </button>
      </div>
    </div>
  );
}
