"""Analytics API endpoints."""
import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
from typing import Dict, List, Any
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.extraction import Extraction
from app.models.field_correction import FieldCorrection
from app.models.lease import Lease

# Path to accuracy tracking data (relative to project root)
DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"

router = APIRouter()


@router.get("/metrics")
async def get_analytics_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get overall analytics metrics.
    
    Returns:
        Dictionary with overall accuracy, total extractions, corrections, etc.
    """
    # Total extractions
    total_extractions = db.query(func.count(Extraction.id)).scalar()
    
    # Total corrections
    total_corrections = db.query(func.count(FieldCorrection.id)).scalar()
    
    # Calculate overall accuracy
    # Count accepted corrections (corrections where is_correct = True or correction_type = 'accept')
    correct_corrections = db.query(func.count(FieldCorrection.id)).filter(
        FieldCorrection.correction_type == 'accept'
    ).scalar()
    
    overall_accuracy = correct_corrections / total_corrections if total_corrections > 0 else 0

    # Average confidence across all extractions
    # Since confidence is JSON, we need to calculate this in Python
    extractions = db.query(Extraction.confidence).filter(Extraction.confidence.isnot(None)).all()
    all_confidences = []
    for (confidence_json,) in extractions:
        if confidence_json and isinstance(confidence_json, dict):
            all_confidences.extend(confidence_json.values())

    avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
    
    # Determine trend (compare last 30 days vs previous 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    sixty_days_ago = datetime.utcnow() - timedelta(days=60)
    
    recent_accuracy = db.query(func.count(FieldCorrection.id)).filter(
        FieldCorrection.correction_type == 'accept',
        FieldCorrection.created_at >= thirty_days_ago
    ).scalar()
    
    recent_total = db.query(func.count(FieldCorrection.id)).filter(
        FieldCorrection.created_at >= thirty_days_ago
    ).scalar()
    
    previous_accuracy = db.query(func.count(FieldCorrection.id)).filter(
        FieldCorrection.correction_type == 'accept',
        FieldCorrection.created_at >= sixty_days_ago,
        FieldCorrection.created_at < thirty_days_ago
    ).scalar()
    
    previous_total = db.query(func.count(FieldCorrection.id)).filter(
        FieldCorrection.created_at >= sixty_days_ago,
        FieldCorrection.created_at < thirty_days_ago
    ).scalar()
    
    recent_rate = recent_accuracy / recent_total if recent_total > 0 else 0
    previous_rate = previous_accuracy / previous_total if previous_total > 0 else 0
    
    trend = 'up' if recent_rate >= previous_rate else 'down'
    
    return {
        "overallAccuracy": overall_accuracy,
        "totalExtractions": total_extractions,
        "totalCorrections": total_corrections,
        "avgConfidence": avg_confidence,
        "trend": trend,
    }


@router.get("/fields")
async def get_field_analytics(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Get analytics by field.
    
    Returns:
        List of field statistics with accuracy, corrections, and confidence.
    """
    # Get all field corrections grouped by field_path
    corrections_by_field = db.query(
        FieldCorrection.field_path,
        func.count(FieldCorrection.id).label('total_corrections'),
        func.sum(
            case(
                (FieldCorrection.correction_type == 'accept', 1),
                else_=0
            )
        ).label('correct_count')
    ).group_by(FieldCorrection.field_path).all()
    
    field_stats = []
    
    for field_path, total_corrections, correct_count in corrections_by_field:
        accuracy = correct_count / total_corrections if total_corrections > 0 else 0

        # Get average confidence for this field by parsing JSON
        extractions = db.query(Extraction.confidence).filter(
            Extraction.confidence.isnot(None)
        ).all()

        field_confidences = []
        for (confidence_json,) in extractions:
            if confidence_json and isinstance(confidence_json, dict):
                if field_path in confidence_json:
                    field_confidences.append(confidence_json[field_path])

        avg_confidence = sum(field_confidences) / len(field_confidences) if field_confidences else 0

        field_stats.append({
            "field": field_path,
            "accuracy": accuracy,
            "corrections": total_corrections,
            "avgConfidence": avg_confidence,
        })
    
    # Sort by accuracy (lowest first - fields that need attention)
    field_stats.sort(key=lambda x: x['accuracy'])
    
    return field_stats


@router.get("/recent-corrections")
async def get_recent_corrections(
    limit: int = 50,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get recent corrections for review.
    
    Args:
        limit: Maximum number of corrections to return
        
    Returns:
        List of recent corrections with context
    """
    corrections = db.query(FieldCorrection)\
        .order_by(desc(FieldCorrection.created_at))\
        .limit(limit)\
        .all()
    
    result = []
    for correction in corrections:
        # Get the lease filename for context
        extraction = db.query(Extraction).filter(
            Extraction.id == correction.extraction_id
        ).first()
        
        if extraction:
            lease = db.query(Lease).filter(
                Lease.id == extraction.lease_id
            ).first()
            
            result.append({
                "id": correction.id,
                "field_path": correction.field_path,
                "original_value": correction.original_value,
                "corrected_value": correction.corrected_value,
                "correction_type": correction.correction_type,
                "notes": correction.notes,
                "created_at": correction.created_at.isoformat(),
                "lease_filename": lease.original_filename if lease else "Unknown",
            })
    
    return result


@router.get("/insights")
async def get_insights(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Get AI-generated insights and recommendations.
    
    Returns:
        List of insights with severity and recommendations
    """
    # Get field statistics
    field_stats = await get_field_analytics(db)
    
    insights = []
    
    for field in field_stats:
        if field['accuracy'] < 0.7 and field['corrections'] > 10:
            insights.append({
                "type": "critical",
                "field": field['field'],
                "title": f"{field['field'].replace('_', ' ').title()} needs immediate attention",
                "message": f"Only {field['accuracy']*100:.1f}% accuracy with {field['corrections']} corrections. "
                          f"Consider adding few-shot examples or improving prompt guidance.",
                "recommendation": "Add 3-5 high-quality examples of correct extractions for this field.",
            })
        elif field['accuracy'] < 0.8 and field['corrections'] > 5:
            insights.append({
                "type": "warning",
                "field": field['field'],
                "title": f"{field['field'].replace('_', ' ').title()} accuracy declining",
                "message": f"{field['accuracy']*100:.1f}% accuracy with {field['corrections']} corrections. "
                          f"The model may struggle with edge cases.",
                "recommendation": "Review recent corrections to identify patterns and adjust prompt.",
            })
        elif field['accuracy'] > 0.9:
            insights.append({
                "type": "success",
                "field": field['field'],
                "title": f"{field['field'].replace('_', ' ').title()} performing well",
                "message": f"{field['accuracy']*100:.1f}% accuracy with only {field['corrections']} corrections. "
                          f"Current approach is effective.",
                "recommendation": "Use this field's prompt structure as a template for other fields.",
            })
    
    return insights


@router.get("/accuracy-history")
async def get_accuracy_history() -> List[Dict[str, Any]]:
    """Return the accuracy history from data/accuracy_history.json."""
    history_path = DATA_DIR / "accuracy_history.json"
    if not history_path.exists():
        return []
    with open(history_path) as f:
        return json.load(f)


@router.get("/accuracy-run/{run_id}")
async def get_accuracy_run(run_id: str) -> Dict[str, Any]:
    """Return detailed results for a specific accuracy run."""
    # Look for matching file in data/runs/
    runs_dir = DATA_DIR / "runs"
    if not runs_dir.exists():
        raise HTTPException(status_code=404, detail="Runs directory not found")

    for file in runs_dir.glob(f"{run_id}*.json"):
        with open(file) as f:
            return json.load(f)

    raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
