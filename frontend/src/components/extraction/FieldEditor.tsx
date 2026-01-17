'use client';

import { FieldDefinition, Citation } from '@/types';
import { getConfidenceColor } from '@/lib/utils';
import { Info } from 'lucide-react';

interface FieldEditorProps {
  field: FieldDefinition;
  value: any;
  confidence?: number;
  reasoning?: string;
  citation?: Citation;
  onChange: (value: any) => void;
}

export function FieldEditor({
  field,
  value,
  confidence,
  reasoning,
  citation,
  onChange,
}: FieldEditorProps) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    onChange(newValue === '' ? null : newValue);
  };

  const displayValue = value ?? '';

  return (
    <div className="border-b border-gray-200 pb-4 last:border-b-0">
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700">
            {field.label}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </label>
          <p className="text-xs text-gray-500 mt-1">{field.description}</p>
        </div>
        {confidence !== undefined && (
          <div className="ml-4 text-right">
            <span className={`text-xs font-medium ${getConfidenceColor(confidence)}`}>
              {(confidence * 100).toFixed(0)}% confident
            </span>
          </div>
        )}
      </div>

      {/* Input field */}
      <div className="mt-2">
        {field.type === 'text' || field.type === 'address' ? (
          <textarea
            value={displayValue}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={2}
            placeholder={`Enter ${field.label.toLowerCase()}`}
          />
        ) : (
          <input
            type={field.type === 'number' || field.type === 'currency' || field.type === 'percentage' || field.type === 'area' ? 'number' : field.type === 'date' ? 'date' : 'text'}
            value={displayValue}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder={`Enter ${field.label.toLowerCase()}`}
          />
        )}
      </div>

      {/* Metadata: reasoning and citation */}
      {(reasoning || citation) && (
        <div className="mt-3 space-y-2">
          {reasoning && (
            <details className="group">
              <summary className="flex items-center text-xs text-gray-600 cursor-pointer hover:text-gray-900">
                <Info className="h-3 w-3 mr-1" />
                <span className="font-medium">AI Reasoning</span>
              </summary>
              <div className="mt-2 p-3 bg-gray-50 rounded-md text-xs text-gray-700">
                {reasoning}
              </div>
            </details>
          )}
          {citation && (
            <details className="group">
              <summary className="flex items-center text-xs text-gray-600 cursor-pointer hover:text-gray-900">
                <Info className="h-3 w-3 mr-1" />
                <span className="font-medium">Source Citation (Page {citation.page})</span>
              </summary>
              <div className="mt-2 p-3 bg-blue-50 rounded-md text-xs text-gray-700">
                <p className="italic">&ldquo;{citation.quote}&rdquo;</p>
              </div>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
