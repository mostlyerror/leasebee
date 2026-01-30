"""Progress tracking for long-running extraction operations."""
import time
import asyncio
from typing import Dict, Optional, Callable
from datetime import datetime
from enum import Enum


class ExtractionStage(str, Enum):
    """Stages of the extraction process."""
    UPLOADING = "uploading"
    EXTRACTING_TEXT = "extracting_text"
    ANALYZING = "analyzing"
    PARSING = "parsing"
    VALIDATING = "validating"
    SAVING = "saving"
    COMPLETE = "complete"


STAGE_WEIGHTS = {
    ExtractionStage.UPLOADING: 5,
    ExtractionStage.EXTRACTING_TEXT: 10,
    ExtractionStage.ANALYZING: 60,  # Claude API is the longest
    ExtractionStage.PARSING: 10,
    ExtractionStage.VALIDATING: 10,
    ExtractionStage.SAVING: 5,
}

STAGE_DESCRIPTIONS = {
    ExtractionStage.UPLOADING: "Uploading PDF to storage",
    ExtractionStage.EXTRACTING_TEXT: "Reading PDF content",
    ExtractionStage.ANALYZING: "AI analyzing lease document",
    ExtractionStage.PARSING: "Processing extraction results",
    ExtractionStage.VALIDATING: "Validating extracted data",
    ExtractionStage.SAVING: "Saving to database",
    ExtractionStage.COMPLETE: "Complete!",
}

# Educational tips to show during analysis
EDUCATIONAL_TIPS = [
    "💡 Lease abstraction can save 70-90% of review time compared to manual extraction.",
    "📄 Commercial leases typically contain 40+ key data points across 11 categories.",
    "🤖 AI can identify critical terms like rent escalations, renewal options, and termination clauses.",
    "⚖️ Accurate lease abstraction helps ensure compliance and avoid costly oversights.",
    "📊 Extracted data can be exported directly to Excel or your lease management system.",
    "🔍 The AI looks for specific sections: Parties, Term, Rent, Use, Maintenance, and more.",
    "⏱️  Manual lease review takes 2-4 hours. AI extraction takes under 2 minutes.",
    "🎯 High confidence scores (>90%) indicate clear, unambiguous text in the document.",
    "📑 The system extracts not just values, but also the reasoning and source citations.",
    "🔄 Your feedback on extractions helps improve accuracy for future documents.",
]


class ProgressTracker:
    """Tracks progress of extraction operations."""
    
    def __init__(self, operation_id: str):
        self.operation_id = operation_id
        self.current_stage = ExtractionStage.UPLOADING
        self.stage_start_time = time.time()
        self.start_time = time.time()
        self.completed_stages: set = set()
        self.estimated_total_seconds = 60  # Initial estimate
        self.current_tip_index = 0
        self.last_tip_change = time.time()
        self._callbacks: list[Callable] = []
        
    def _notify(self):
        """Notify all registered callbacks of progress update."""
        progress_data = self.get_progress()
        for callback in self._callbacks:
            try:
                callback(progress_data)
            except Exception:
                pass
                
    def on_progress(self, callback: Callable):
        """Register a callback for progress updates."""
        self._callbacks.append(callback)
        
    def advance_stage(self, stage: ExtractionStage):
        """Move to the next stage."""
        if self.current_stage != stage:
            self.completed_stages.add(self.current_stage)
            self.current_stage = stage
            self.stage_start_time = time.time()
            self._update_estimate()
            self._notify()
            
    def _update_estimate(self):
        """Update time estimate based on actual performance."""
        elapsed = time.time() - self.start_time
        
        # Calculate completed weight
        completed_weight = sum(STAGE_WEIGHTS.get(s, 0) for s in self.completed_stages)
        current_stage_progress = self._get_current_stage_progress()
        current_stage_weight = STAGE_WEIGHTS.get(self.current_stage, 0) * current_stage_progress
        
        total_weight = sum(STAGE_WEIGHTS.values())
        progress_weight = completed_weight + current_stage_weight
        
        if progress_weight > 0:
            # Estimate: if X% of work took Y seconds, total will be Y/X%
            estimated_total = (elapsed / progress_weight) * total_weight
            self.estimated_total_seconds = max(estimated_total, elapsed + 5)  # At least 5s remaining
            
    def _get_current_stage_progress(self) -> float:
        """Get progress within current stage (0-1)."""
        stage_elapsed = time.time() - self.stage_start_time
        
        # Stage-specific progress estimates
        if self.current_stage == ExtractionStage.ANALYZING:
            # Claude API typically takes 30-90 seconds
            return min(stage_elapsed / 60, 0.95)  # Cap at 95% until actually done
        elif self.current_stage == ExtractionStage.EXTRACTING_TEXT:
            return min(stage_elapsed / 3, 0.9)
        else:
            return min(stage_elapsed / 2, 0.9)
            
    def get_progress(self) -> dict:
        """Get current progress information."""
        elapsed = time.time() - self.start_time
        
        # Calculate overall percentage
        completed_weight = sum(STAGE_WEIGHTS.get(s, 0) for s in self.completed_stages)
        current_stage_progress = self._get_current_stage_progress()
        current_stage_weight = STAGE_WEIGHTS.get(self.current_stage, 0) * current_stage_progress
        
        total_weight = sum(STAGE_WEIGHTS.values())
        percentage = int(((completed_weight + current_stage_weight) / total_weight) * 100)
        
        # Time estimates
        remaining = max(0, self.estimated_total_seconds - elapsed)
        
        # Rotate tip every 8 seconds
        if time.time() - self.last_tip_change > 8:
            self.current_tip_index = (self.current_tip_index + 1) % len(EDUCATIONAL_TIPS)
            self.last_tip_change = time.time()
            
        return {
            "operation_id": self.operation_id,
            "stage": self.current_stage.value,
            "stage_description": STAGE_DESCRIPTIONS[self.current_stage],
            "percentage": min(percentage, 99),  # Cap at 99% until complete
            "elapsed_seconds": int(elapsed),
            "estimated_remaining_seconds": int(remaining),
            "tip": EDUCATIONAL_TIPS[self.current_tip_index],
            "completed_stages": [s.value for s in self.completed_stages],
        }


# Global progress store
_progress_trackers: Dict[str, ProgressTracker] = {}


def get_tracker(operation_id: str) -> Optional[ProgressTracker]:
    """Get a progress tracker by ID."""
    return _progress_trackers.get(operation_id)


def create_tracker(operation_id: str) -> ProgressTracker:
    """Create a new progress tracker."""
    tracker = ProgressTracker(operation_id)
    _progress_trackers[operation_id] = tracker
    return tracker


def remove_tracker(operation_id: str):
    """Remove a progress tracker."""
    _progress_trackers.pop(operation_id, None)
