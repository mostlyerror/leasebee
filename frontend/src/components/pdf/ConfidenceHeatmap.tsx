'use client';

import { useState } from 'react';
import { AlertCircle, CheckCircle2, HelpCircle, Eye, EyeOff } from 'lucide-react';

interface HeatmapField {
  fieldPath: string;
  label: string;
  page: number;
  confidence: number;
  boundingBox?: {
    x0: number;
    y0: number;
    x1: number;
    y1: number;
  };
}

interface ConfidenceHeatmapProps {
  fields: HeatmapField[];
  activeField: string | null;
  onFieldClick: (fieldPath: string) => void;
  scale: number;
}

function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.9) return 'bg-green-500';
  if (confidence >= 0.7) return 'bg-yellow-400';
  return 'bg-red-500';
}

function getConfidenceBgColor(confidence: number): string {
  if (confidence >= 0.9) return 'bg-green-500/40';
  if (confidence >= 0.7) return 'bg-yellow-400/40';
  return 'bg-red-500/40';
}

function getConfidenceBorderColor(confidence: number): string {
  if (confidence >= 0.9) return 'border-green-600';
  if (confidence >= 0.7) return 'border-yellow-500';
  return 'border-red-600';
}

function getConfidenceLabel(confidence: number): string {
  if (confidence >= 0.9) return 'High';
  if (confidence >= 0.7) return 'Medium';
  return 'Low';
}

export function ConfidenceHeatmap({ fields, activeField, onFieldClick, scale }: ConfidenceHeatmapProps) {
  const [hoveredField, setHoveredField] = useState<string | null>(null);

  const fieldsWithBoxes = fields.filter((f) => f.boundingBox);

  // Filter to show only active field if one is selected AND it has a bounding box
  // Otherwise show all fields
  const visibleFields = activeField && fieldsWithBoxes.some(f => f.fieldPath === activeField)
    ? fieldsWithBoxes.filter((f) => f.fieldPath === activeField)
    : fieldsWithBoxes;

  return (
    <>
      {/* Heatmap Overlays */}
      {visibleFields.map((field) => {
        const isActive = activeField === field.fieldPath;
        const isHovered = hoveredField === field.fieldPath;
        const bb = field.boundingBox!;

        // Get background color based on state
        const bgColor = isActive
          ? 'rgba(59, 130, 246, 0.6)'
          : field.confidence >= 0.9
            ? 'rgba(34, 197, 94, 0.4)'  // green
            : field.confidence >= 0.7
              ? 'rgba(250, 204, 21, 0.4)'  // yellow
              : 'rgba(239, 68, 68, 0.4)';  // red

        const borderColor = isActive
          ? '#2563eb'  // blue-600
          : field.confidence >= 0.9
            ? '#16a34a'  // green-600
            : field.confidence >= 0.7
              ? '#eab308'  // yellow-500
              : '#dc2626';  // red-600

        return (
          <div
            key={field.fieldPath}
            className={`absolute cursor-pointer transition-all duration-200 rounded ${
              isActive
                ? 'ring-[6px] ring-blue-500 z-20 shadow-2xl shadow-blue-500/50'
                : ''
            } ${isHovered ? 'z-10 brightness-125 scale-105' : 'z-0'}`}
            style={{
              left: `${bb.x0 * scale}px`,
              top: `${bb.y0 * scale}px`,
              width: `${(bb.x1 - bb.x0) * scale}px`,
              height: `${(bb.y1 - bb.y0) * scale}px`,
              backgroundColor: bgColor,
              border: `${isActive ? 6 : 3}px solid ${borderColor}`,
            }}
            onClick={() => onFieldClick(field.fieldPath)}
            onMouseEnter={() => setHoveredField(field.fieldPath)}
            onMouseLeave={() => setHoveredField(null)}
          >
            {/* Tooltip on hover */}
            {isHovered && (
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-slate-900 text-white text-xs rounded whitespace-nowrap z-30 pointer-events-none">
                <span className="font-medium">{field.label}</span>
                <span className="ml-2 opacity-80">
                  {getConfidenceLabel(field.confidence)} ({Math.round(field.confidence * 100)}%)
                </span>
                <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-900" />
              </div>
            )}
          </div>
        );
      })}
    </>
  );
}

export function HeatmapLegend({ 
  onToggle, 
  isVisible 
}: { 
  onToggle: () => void; 
  isVisible: boolean;
}) {
  const legendItems = [
    { color: 'bg-green-500', label: 'High Confidence', range: '90-100%', icon: CheckCircle2 },
    { color: 'bg-yellow-400', label: 'Medium Confidence', range: '70-89%', icon: HelpCircle },
    { color: 'bg-red-500', label: 'Low Confidence', range: '< 70%', icon: AlertCircle },
  ];

  return (
    <div className="bg-white rounded-lg shadow-md border border-slate-200 p-3">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
          Confidence Heatmap
        </h4>
        <button
          onClick={onToggle}
          className="text-slate-400 hover:text-slate-600 transition-colors"
          title={isVisible ? 'Hide heatmap' : 'Show heatmap'}
        >
          {isVisible ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
        </button>
      </div>
      
      {isVisible && (
        <div className="space-y-1.5">
          {legendItems.map((item) => (
            <div key={item.label} className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-sm ${item.color}`} />
              <span className="text-xs text-slate-600 flex-1">{item.label}</span>
              <span className="text-xs text-slate-400">{item.range}</span>
            </div>
          ))}
        </div>
      )}
      
      {!isVisible && (
        <p className="text-xs text-slate-500 italic">
          Click the eye icon to show confidence overlay
        </p>
      )}
    </div>
  );
}
