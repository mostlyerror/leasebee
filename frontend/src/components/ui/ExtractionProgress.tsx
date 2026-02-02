'use client';

import { useEffect, useState } from 'react';
import { Loader2, FileText, Brain, CheckCircle2, Sparkles, Clock, ChevronDown, ChevronUp, Activity } from 'lucide-react';

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

// Stage-specific context messaging
const STAGE_CONTEXT: Record<string, string> = {
  uploading: 'Quick step - just a few seconds',
  extracting_text: 'Reading the PDF content',
  analyzing: 'This is the longest step - usually 20-30 seconds',
  parsing: 'Almost done! Processing the extracted data',
  validating: 'Final checks - nearly there',
  saving: 'Finishing up',
};

function formatTime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}m ${secs}s`;
}

// Get reassurance message based on elapsed time
function getReassuranceMessage(elapsedSeconds: number, stage: string): string {
  if (elapsedSeconds < 20) {
    return 'Processing... right on track';
  } else if (elapsedSeconds < 45) {
    return 'Analyzing document details... almost there';
  } else if (elapsedSeconds < 60) {
    return 'Finishing up the final fields...';
  } else if (elapsedSeconds < 90) {
    return 'This document is taking a bit longer than usual, but we\'re still making progress. Hang tight!';
  } else {
    return 'Still processing... complex documents can take up to 2 minutes.';
  }
}

// Determine health status based on elapsed time
function getHealthStatus(elapsedSeconds: number): 'good' | 'slow' {
  return elapsedSeconds < 60 ? 'good' : 'slow';
}

export function ExtractionProgress({ leaseId, onComplete }: ExtractionProgressProps) {
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [leaseStatus, setLeaseStatus] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [perceivedProgress, setPerceivedProgress] = useState(0);
  const [activityLog, setActivityLog] = useState<string[]>([]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    let checkCounter = 0;
    let isActive = true;
    let perceivedProgressInterval: NodeJS.Timeout;

    // Perceived progress - fills to 10% in first 5 seconds
    let perceivedValue = 0;
    perceivedProgressInterval = setInterval(() => {
      if (perceivedValue < 10 && !progress) {
        perceivedValue += 1;
        setPerceivedProgress(perceivedValue);
      }
    }, 500);

    // Add to activity log
    const logActivity = (message: string) => {
      setActivityLog((prev) => [...prev.slice(-9), `${new Date().toLocaleTimeString()}: ${message}`]);
    };

    logActivity('Starting extraction process...');

    setTimeout(() => {
      if (isActive && !progress) {
        logActivity('Connecting to AI service...');
      }
    }, 1000);

    setTimeout(() => {
      if (isActive && !progress) {
        logActivity('Connected! Preparing document...');
      }
    }, 2000);

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

        // Log stage changes
        if (!progress || progress.stage !== data.stage) {
          logActivity(`Stage: ${data.stage_description} (${data.percentage}%)`);
        }

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

    // Start polling every 5 seconds
    interval = setInterval(pollProgress, 5000);
    pollProgress(); // Initial call

    return () => {
      isActive = false;
      if (interval) clearInterval(interval);
      if (perceivedProgressInterval) clearInterval(perceivedProgressInterval);
    };
  }, [leaseId, onComplete]); // Remove 'progress' dependency

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
        <div className="flex flex-col items-center justify-center py-8">
          {/* Health Indicator */}
          <div className="flex items-center gap-2 mb-4 text-sm font-medium text-green-600">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span>System ready</span>
          </div>

          {/* Expected Time Banner */}
          <div className="mb-6 px-4 py-2 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-900 font-medium">
              ⏱️ Expected time: <span className="font-bold">30-60 seconds</span>
            </p>
          </div>

          <div className="relative mb-6">
            <div className="w-20 h-20 bg-amber-100 rounded-full flex items-center justify-center">
              <Loader2 className="w-10 h-10 animate-spin text-amber-600" />
            </div>
            <div className="absolute -inset-1 bg-gradient-to-r from-amber-200 to-orange-200 rounded-full blur opacity-30 animate-pulse" />
          </div>

          <h3 className="text-xl font-semibold text-slate-900 mb-2">
            {activityLog.length > 0 ? activityLog[activityLog.length - 1].split(': ')[1] : 'Starting Analysis'}
          </h3>

          <p className="text-slate-600 text-center max-w-md mb-4">
            Preparing to extract data from your lease document
          </p>

          {/* Perceived Progress Bar */}
          <div className="w-full max-w-md mb-4">
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-amber-500 transition-all duration-500 ease-out"
                style={{ width: `${perceivedProgress}%` }}
              />
            </div>
          </div>

          {/* Expandable Details */}
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="mt-4 flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 transition-colors"
          >
            {showDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            <span>What's happening?</span>
          </button>

          {showDetails && (
            <div className="mt-4 w-full max-w-md p-4 bg-slate-50 rounded-lg border border-slate-200">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="w-4 h-4 text-slate-600" />
                <span className="text-sm font-medium text-slate-900">Activity Log</span>
              </div>
              <div className="space-y-1 text-xs font-mono text-slate-600">
                {activityLog.map((log, i) => (
                  <div key={i}>{log}</div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  const currentStageColor = STAGE_COLORS[progress.stage] || 'bg-blue-500';
  const isAnalyzing = progress.stage === 'analyzing';
  const healthStatus = getHealthStatus(progress.elapsed_seconds);
  const reassuranceMessage = getReassuranceMessage(progress.elapsed_seconds, progress.stage);
  const stageContext = STAGE_CONTEXT[progress.stage] || '';
  const totalEstimatedTime = progress.elapsed_seconds + progress.estimated_remaining_seconds;

  return (
    <div className="w-full max-w-2xl mx-auto p-6 bg-white rounded-xl shadow-lg border">
      {/* Health Indicator & Expected Time */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-sm font-medium">
          <div className={`w-2 h-2 rounded-full animate-pulse ${
            healthStatus === 'good' ? 'bg-green-500' : 'bg-yellow-500'
          }`} />
          <span className={healthStatus === 'good' ? 'text-green-600' : 'text-yellow-600'}>
            {healthStatus === 'good' ? 'On track' : 'Taking longer than usual'}
          </span>
        </div>
        <div className="px-3 py-1 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-900 font-medium">
            Expected: <span className="font-bold">30-60s</span>
          </p>
        </div>
      </div>

      {/* Reassurance Message */}
      <div className="mb-4 p-3 bg-slate-50 border border-slate-200 rounded-lg">
        <p className="text-sm text-slate-700 text-center font-medium">
          {reassuranceMessage}
        </p>
      </div>

      {/* Header */}
      <div className="flex items-center gap-3 mb-2">
        <div className={`p-3 rounded-full ${currentStageColor} bg-opacity-10`}>
          {isAnalyzing ? (
            <Brain className={`w-8 h-8 ${currentStageColor.replace('bg-', 'text-')}`} />
          ) : (
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          )}
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">
            {progress.stage_description}
          </h3>
          <p className="text-sm text-gray-500">
            {stageContext}
          </p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-slate-900">
            {progress.percentage}%
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

      {/* Time Estimate - More Prominent */}
      <div className="flex items-center justify-between mb-4 p-3 bg-slate-50 rounded-lg border border-slate-200">
        <div className="flex items-center gap-2">
          <Clock className="w-5 h-5 text-slate-600" />
          <div>
            <p className="text-xs text-slate-500">Elapsed</p>
            <p className="text-lg font-bold text-slate-900">{formatTime(progress.elapsed_seconds)}</p>
          </div>
        </div>
        {progress.estimated_remaining_seconds > 0 && (
          <>
            <div className="text-center">
              <p className="text-xs text-slate-500">Remaining</p>
              <p className="text-lg font-bold text-blue-600">
                ~{formatTime(progress.estimated_remaining_seconds)}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs text-slate-500">Total</p>
              <p className="text-lg font-bold text-slate-700">
                ~{formatTime(totalEstimatedTime)}
              </p>
            </div>
          </>
        )}
      </div>

      {/* Educational Tip */}
      <div className="p-4 bg-blue-50 rounded-lg border border-blue-100 mb-4">
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

      {/* Expandable Technical Details */}
      <div className="border-t border-slate-200 pt-4">
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="w-full flex items-center justify-center gap-2 text-sm text-slate-600 hover:text-slate-900 transition-colors"
        >
          {showDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          <span>What's happening?</span>
        </button>

        {showDetails && (
          <div className="mt-4 p-4 bg-slate-50 rounded-lg border border-slate-200">
            <div className="flex items-center gap-2 mb-3">
              <Activity className="w-4 h-4 text-slate-600" />
              <span className="text-sm font-medium text-slate-900">Activity Log</span>
            </div>
            <div className="space-y-1 text-xs font-mono text-slate-600 max-h-40 overflow-y-auto">
              {activityLog.map((log, i) => (
                <div key={i} className="py-0.5">{log}</div>
              ))}
            </div>
            <div className="mt-3 pt-3 border-t border-slate-200">
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <p className="text-slate-500 mb-1">Completed Stages</p>
                  <p className="font-medium text-slate-900">{progress.completed_stages.length} / 6</p>
                </div>
                <div>
                  <p className="text-slate-500 mb-1">Current Stage</p>
                  <p className="font-medium text-slate-900">{progress.stage}</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Fun Animation for AI Stage */}
      {isAnalyzing && (
        <div className="mt-4 flex justify-center">
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
