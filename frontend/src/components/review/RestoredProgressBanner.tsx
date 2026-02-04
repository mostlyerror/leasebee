'use client';

import { Clock, X } from 'lucide-react';
import { formatTimeAgo } from '@/lib/utils';

interface RestoredProgressBannerProps {
  savedAt: number | null;
  onDismiss: () => void;
  onDiscard: () => void;
}

export function RestoredProgressBanner({
  savedAt,
  onDismiss,
  onDiscard,
}: RestoredProgressBannerProps) {
  const timeAgo = savedAt ? formatTimeAgo(savedAt) : 'recently';

  return (
    <div className="bg-blue-50 border-b border-blue-200 px-8 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Clock className="w-5 h-5 text-blue-600" />
          <div>
            <p className="text-sm font-medium text-blue-900">
              Review progress restored from {timeAgo}
            </p>
            <p className="text-xs text-blue-700">
              Your previous accept/reject/edit choices have been recovered.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onDiscard}
            className="px-3 py-1 text-sm text-blue-700 hover:bg-blue-100 rounded transition-colors"
          >
            Discard & Start Fresh
          </button>
          <button
            onClick={onDismiss}
            className="text-blue-400 hover:text-blue-600 transition-colors"
            aria-label="Dismiss banner"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
