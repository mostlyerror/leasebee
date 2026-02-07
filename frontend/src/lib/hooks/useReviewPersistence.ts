'use client';

import { useState, useEffect, useCallback } from 'react';

const STORAGE_KEY_PREFIX = 'leasebee_review_progress_';
const STORAGE_VERSION = 1;

interface FieldFeedback {
  fieldPath: string;
  isCorrect: boolean;
  correctedValue?: any;
  notes?: string;
}

interface ProgressData {
  leaseId: number;
  extractionId: number;
  timestamp: number;
  feedback: Record<string, FieldFeedback>;
  version: number;
}

interface UseReviewPersistenceOptions {
  leaseId: number;
  extractionId: number | undefined;
  feedback: Record<string, FieldFeedback>;
  setFeedback: (feedback: Record<string, FieldFeedback>) => void;
  debounceMs?: number;
  maxAgeMs?: number;
}

interface UseReviewPersistenceReturn {
  isRestored: boolean;
  savedAt: number | null;
  dismissRestoredBanner: () => void;
  clearProgress: () => void;
  isSaving: boolean;
  lastSaved: number | null;
}

/**
 * Generate lease-specific storage key
 */
function getStorageKey(leaseId: number): string {
  return `${STORAGE_KEY_PREFIX}${leaseId}`;
}

/**
 * Safely get data from localStorage with error handling
 */
function safeLocalStorageGet(key: string): ProgressData | null {
  try {
    const item = localStorage.getItem(key);
    if (!item) return null;
    return JSON.parse(item) as ProgressData;
  } catch (error) {
    console.warn('Failed to read from localStorage:', error);
    return null;
  }
}

/**
 * Safely set data in localStorage with error handling
 */
function safeLocalStorageSet(key: string, value: ProgressData): boolean {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch (error) {
    console.warn('Failed to write to localStorage:', error);
    return false;
  }
}

/**
 * Validate progress data before restoring
 */
function isValidProgressData(
  data: ProgressData | null,
  leaseId: number,
  extractionId: number,
  maxAgeMs: number
): data is ProgressData {
  if (!data) return false;

  // Check data structure
  if (
    typeof data.leaseId !== 'number' ||
    typeof data.extractionId !== 'number' ||
    typeof data.timestamp !== 'number' ||
    typeof data.feedback !== 'object' ||
    typeof data.version !== 'number'
  ) {
    return false;
  }

  // Check version
  if (data.version !== STORAGE_VERSION) {
    return false;
  }

  // Check lease ID matches
  if (data.leaseId !== leaseId) {
    return false;
  }

  // Check extraction ID matches (detect re-extraction)
  if (data.extractionId !== extractionId) {
    return false;
  }

  // Check staleness (default: 7 days)
  const age = Date.now() - data.timestamp;
  if (age > maxAgeMs) {
    return false;
  }

  return true;
}

/**
 * Hook for persisting review progress in localStorage
 */
export function useReviewPersistence(
  options: UseReviewPersistenceOptions
): UseReviewPersistenceReturn {
  const {
    leaseId,
    extractionId,
    feedback,
    setFeedback,
    debounceMs = 500,
    maxAgeMs = 7 * 24 * 60 * 60 * 1000, // 7 days
  } = options;

  const [isRestored, setIsRestored] = useState(false);
  const [savedAt, setSavedAt] = useState<number | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<number | null>(null);

  // Restore on mount (after extractionId loads)
  useEffect(() => {
    if (!extractionId) return; // Wait for extraction data

    const key = getStorageKey(leaseId);
    const data = safeLocalStorageGet(key);

    if (isValidProgressData(data, leaseId, extractionId, maxAgeMs)) {
      setFeedback(data.feedback);
      setSavedAt(data.timestamp);
      setIsRestored(true);
    } else if (data) {
      // Invalid data - clear it
      localStorage.removeItem(key);
    }
  }, [extractionId, leaseId, maxAgeMs, setFeedback]);

  // Debounced auto-save
  useEffect(() => {
    if (!extractionId || Object.keys(feedback).length === 0) return;

    setIsSaving(true);
    const timeoutId = setTimeout(() => {
      const key = getStorageKey(leaseId);
      const success = safeLocalStorageSet(key, {
        leaseId,
        extractionId,
        timestamp: Date.now(),
        feedback,
        version: STORAGE_VERSION,
      });

      if (success) {
        setLastSaved(Date.now());
      }
      setIsSaving(false);
    }, debounceMs);

    return () => {
      clearTimeout(timeoutId);
      setIsSaving(false);
    };
  }, [feedback, leaseId, extractionId, debounceMs]);

  // beforeunload backup save
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (Object.keys(feedback).length > 0 && extractionId) {
        const key = getStorageKey(leaseId);
        safeLocalStorageSet(key, {
          leaseId,
          extractionId,
          timestamp: Date.now(),
          feedback,
          version: STORAGE_VERSION,
        });
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [feedback, leaseId, extractionId]);

  const clearProgress = useCallback(() => {
    const key = getStorageKey(leaseId);
    localStorage.removeItem(key);
    setLastSaved(null);
    setSavedAt(null);
  }, [leaseId]);

  const dismissRestoredBanner = useCallback(() => {
    setIsRestored(false);
  }, []);

  return {
    isRestored,
    savedAt,
    dismissRestoredBanner,
    clearProgress,
    isSaving,
    lastSaved,
  };
}
