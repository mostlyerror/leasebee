'use client';

import { useEffect, useState } from 'react';
import { Loader2, FileText, Brain, CheckCircle2, Sparkles, Clock } from 'lucide-react';

interface ProgressData {
  operation_id: string;
  stage: string;
  stage_description: string;
  percentage: number;
  elapsed_seconds: number;
  estimated_remaining_seconds: number;
  tip: string;
  completed_stages: string[];
}

interface ExtractionProgressProps {
  leaseId: number;
  onComplete?: () => void;
}

const STAGE_ICONS: Record<string, React.ReactNode> = {
  uploading: <FileText className="w-5 h-5" />,
  extracting_text: <FileText className="w-5 h-5" />,
  analyzing: <Brain className="w-5 h-5" />,
  parsing: <Sparkles className="w-5 h-5" />,
  validating: <CheckCircle2 className="w-5 h-5" />,
  saving: <CheckCircle2 className="w-5 h-5" />,
  complete: <CheckCircle2 className="w-5 h-5" />,
};

const STAGE_COLORS: Record<string, string> = {
  uploading: 'bg-blue-500',
  extracting_text: 'bg-blue-500',
  analyzing: 'bg-purple-500',
  parsing: 'bg-indigo-500',
  validating: 'bg-green-500',
  saving: 'bg-green-500',
  complete: 'bg-green-500',
};

function formatTime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}m ${secs}s`;
}

export function ExtractionProgress({ leaseId, onComplete }: ExtractionProgressProps) {
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const pollProgress = async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/extractions/progress/${leaseId}`
        );
        
        if (!response.ok) {
          // If we get a 404, the extraction might be complete
          if (response.status === 404) {
            onComplete?.();
            return;
          }
          throw new Error('Failed to fetch progress');
        }
        
        const data = await response.json();
        setProgress(data);
        
        // Check if complete
        if (data.stage === 'complete' || data.percentage >= 100) {
          setTimeout(() => onComplete?.(), 1000);
          return;
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      }
    };

    // Poll every 1 second
    const interval = setInterval(pollProgress, 1000);
    pollProgress(); // Initial call

    return () => clearInterval(interval);
  }, [leaseId, onComplete]);

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-800">Error tracking progress: {error}</p>
      </div>
    );
  }

  if (!progress) {
    return (
      <div className="flex flex-col items-center justify-center p-8">
        <Loader2 className="w-12 h-12 animate-spin text-blue-600" />
        <p className="mt-4 text-gray-600">Initializing extraction...</p>
      </div>
    );
  }

  const currentStageColor = STAGE_COLORS[progress.stage] || 'bg-blue-500';
  const isAnalyzing = progress.stage === 'analyzing';

  return (
    <div className="w-full max-w-2xl mx-auto p-6 bg-white rounded-xl shadow-lg border">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className={`p-3 rounded-full ${currentStageColor} bg-opacity-10`}>
          {isAnalyzing ? (
            <Brain className={`w-8 h-8 ${currentStageColor.replace('bg-', 'text-')}`} />
          ) : (
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          )}
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            {progress.stage_description}
          </h3>
          <p className="text-sm text-gray-500">
            {progress.percentage}% complete
          </p>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ease-out ${currentStageColor}`}
            style={{ width: `${progress.percentage}%` }}
          />
        </div>
      </div>

      {/* Stage Indicators */}
      <div className="flex justify-between mb-6 text-xs">
        {['uploading', 'extracting_text', 'analyzing', 'parsing', 'saving'].map((stage) => (
          <div
            key={stage}
            className={`flex flex-col items-center gap-1 ${
              progress.completed_stages.includes(stage) || progress.stage === stage
                ? 'text-blue-600'
                : 'text-gray-300'
            }`}
          >
            <div
              className={`w-2 h-2 rounded-full ${
                progress.completed_stages.includes(stage)
                  ? 'bg-green-500'
                  : progress.stage === stage
                  ? currentStageColor
                  : 'bg-gray-300'
              }`}
            />
            <span className="capitalize hidden sm:block">
              {stage.replace('_', ' ')}
            </span>
          </div>
        ))}
      </div>

      {/* Time Estimate */}
      <div className="flex items-center gap-2 mb-4 text-sm text-gray-600">
        <Clock className="w-4 h-4" />
        <span>
          Elapsed: {formatTime(progress.elapsed_seconds)}
          {progress.estimated_remaining_seconds > 0 && (
            <span className="text-gray-400">
              {' '}• About {formatTime(progress.estimated_remaining_seconds)} remaining
            </span>
          )}
        </span>
      </div>

      {/* Educational Tip */}
      <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
        <div className="flex items-start gap-3">
          <Sparkles className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-blue-900 mb-1">
              Did you know?
            </p>
            <p className="text-sm text-blue-700">
              {progress.tip}
            </p>
          </div>
        </div>
      </div>

      {/* Fun Animation for AI Stage */}
      {isAnalyzing && (
        <div className="mt-6 flex justify-center">
          <div className="flex gap-1">
            {[0, 1, 2, 3].map((i) => (
              <div
                key={i}
                className="w-2 h-2 bg-purple-500 rounded-full animate-bounce"
                style={{ animationDelay: `${i * 0.15}s` }}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
