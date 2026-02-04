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
  validating: 'bg-teal-500',
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
  const [leaseStatus, setLeaseStatus] = useState<string | null>(null);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    let checkCounter = 0;
    let isActive = true;

    const checkLeaseStatus = async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/leases/${leaseId}`
        );

        if (response.ok) {
          const lease = await response.json();
          setLeaseStatus(lease.status);

          // If lease failed, show error
          if (lease.status === 'failed') {
            const errorMsg = lease.error_message || 'Extraction failed';

            // Parse common errors for user-friendly messages
            let friendlyError = errorMsg;
            if (errorMsg.includes('credit balance is too low')) {
              friendlyError = 'AI service credits depleted. Please add credits to your Anthropic account to continue processing documents.';
            } else if (errorMsg.includes('timeout') || errorMsg.includes('timed out')) {
              friendlyError = 'Document processing timed out. This may be due to a very large file or temporary service issues.';
            } else if (errorMsg.includes('invalid API key') || errorMsg.includes('authentication')) {
              friendlyError = 'AI service authentication failed. Please check your API key configuration.';
            } else if (errorMsg.includes('rate limit')) {
              friendlyError = 'Too many requests. Please wait a moment before trying again.';
            }

            setError(friendlyError);
            clearInterval(interval);
            return true;
          }

          // If lease completed, check for extraction
          if (lease.status === 'completed') {
            onComplete?.();
            return true;
          }
        }
      } catch (err) {
        console.error('Failed to check lease status:', err);
      }
      return false;
    };

    const checkIfExtractionExists = async () => {
      try {
        // Check if extraction already exists (might have completed before we started polling)
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/extractions/lease/${leaseId}`
        );

        if (response.ok) {
          const extractions = await response.json();
          if (extractions && extractions.length > 0) {
            // Extraction already complete!
            onComplete?.();
            return true;
          }
        }
      } catch (err) {
        // Ignore - extraction might not exist yet
      }
      return false;
    };

    const pollProgress = async () => {
      if (!isActive) return;

      checkCounter++;

      // Every 2 seconds, check lease status and extraction
      if (checkCounter % 2 === 0) {
        const failed = await checkLeaseStatus();
        if (failed) return;

        const isDone = await checkIfExtractionExists();
        if (isDone) return;
      }

      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/extractions/progress/${leaseId}`
        );

        if (!response.ok) {
          // If we get a 404, check if extraction exists or failed
          if (response.status === 404) {
            await checkLeaseStatus();
            const isDone = await checkIfExtractionExists();
            if (isDone) return;
          }
          // Don't throw error, just keep polling
          return;
        }

        const data = await response.json();

        // Always show progress data if we have it
        setProgress(data);

        // Check if complete
        if (data.stage === 'complete' || data.percentage >= 100) {
          clearInterval(interval);
          setTimeout(() => onComplete?.(), 1000);
          return;
        }
      } catch (err) {
        // Don't show error, just keep polling
        console.error('Progress poll error:', err);
      }
    };

    // Start polling
    interval = setInterval(pollProgress, 1000);
    pollProgress(); // Initial call

    return () => {
      isActive = false;
      if (interval) clearInterval(interval);
    };
  }, [leaseId, onComplete]);

  if (error) {
    return (
      <div className="w-full max-w-2xl mx-auto p-6 bg-white rounded-xl shadow-lg border">
        <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-red-900 mb-2">
                Extraction Failed
              </h3>
              <p className="text-sm text-red-800 mb-4">
                {error}
              </p>
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!progress) {
    return (
      <div className="w-full max-w-2xl mx-auto p-6 bg-white rounded-xl shadow-lg border">
        <div className="flex flex-col items-center justify-center py-12">
          <div className="relative">
            <div className="w-20 h-20 bg-amber-100 rounded-full flex items-center justify-center mb-6">
              <Loader2 className="w-10 h-10 animate-spin text-amber-600" />
            </div>
            <div className="absolute -inset-1 bg-gradient-to-r from-amber-200 to-orange-200 rounded-full blur opacity-30 animate-pulse" />
          </div>
          <h3 className="text-xl font-semibold text-slate-900 mb-2">
            Starting Analysis
          </h3>
          <p className="text-slate-600 text-center max-w-md">
            Preparing to extract data from your lease document. This usually takes 20-30 seconds.
          </p>
          <div className="mt-6 flex gap-2">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="w-2 h-2 bg-amber-500 rounded-full animate-bounce"
                style={{ animationDelay: `${i * 0.15}s` }}
              />
            ))}
          </div>
        </div>
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
        {['uploading', 'extracting_text', 'analyzing', 'parsing', 'validating', 'saving'].map((stage) => (
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
              {stage.replace(/_/g, ' ')}
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
