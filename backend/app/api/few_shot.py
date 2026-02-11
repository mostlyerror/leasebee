"""Few-shot example API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.few_shot_example import FewShotExample
from app.models.field_correction import FieldCorrection
from app.models.extraction import Extraction
from app.schemas.pydantic_schemas import (
    FewShotExampleCreate,
    FewShotExampleUpdate,
    FewShotExampleResponse,
)

router = APIRouter()


@router.get("/", response_model=List[FewShotExampleResponse])
async def list_examples(
    field_path: Optional[str] = Query(None, description="Filter by field path"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List few-shot examples with optional filters."""
    query = db.query(FewShotExample)

    if field_path is not None:
        query = query.filter(FewShotExample.field_path == field_path)
    if is_active is not None:
        query = query.filter(FewShotExample.is_active == is_active)

    examples = (
        query.order_by(FewShotExample.quality_score.desc().nullslast())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return examples


@router.post("/", response_model=FewShotExampleResponse, status_code=status.HTTP_201_CREATED)
async def create_example(
    data: FewShotExampleCreate,
    db: Session = Depends(get_db),
):
    """Create a few-shot example manually."""
    example = FewShotExample(
        field_path=data.field_path,
        source_text=data.source_text,
        correct_value=data.correct_value,
        reasoning=data.reasoning,
        quality_score=data.quality_score,
    )
    db.add(example)
    db.commit()
    db.refresh(example)
    return example


@router.post(
    "/from-correction/{correction_id}",
    response_model=FewShotExampleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def promote_correction(
    correction_id: int,
    db: Session = Depends(get_db),
):
    """Promote a FieldCorrection to a FewShotExample.

    Loads the correction and its extraction's citation as source_text.
    """
    correction = (
        db.query(FieldCorrection)
        .filter(FieldCorrection.id == correction_id)
        .first()
    )
    if not correction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Correction not found",
        )

    # Check if already promoted
    existing = (
        db.query(FewShotExample)
        .filter(FewShotExample.created_from_correction_id == correction_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This correction has already been promoted to an example",
        )

    # Get the extraction to find citation source text
    extraction = (
        db.query(Extraction)
        .filter(Extraction.id == correction.extraction_id)
        .first()
    )

    source_text = ""
    if extraction and extraction.citations:
        citation = extraction.citations.get(correction.field_path)
        if citation and isinstance(citation, dict):
            quote = citation.get("quote", "")
            page = citation.get("page", "")
            source_text = f"Page {page}: {quote}" if page else quote

    # Fall back to original value if no citation
    if not source_text and correction.original_value:
        source_text = correction.original_value

    example = FewShotExample(
        field_path=correction.field_path,
        source_text=source_text or "No source text available",
        correct_value=correction.corrected_value or correction.original_value or "",
        reasoning=correction.original_reasoning,
        quality_score=1.0 if correction.correction_type == "edit" else 0.8,
        created_from_correction_id=correction_id,
    )
    db.add(example)
    db.commit()
    db.refresh(example)
    return example


@router.patch("/{example_id}", response_model=FewShotExampleResponse)
async def update_example(
    example_id: int,
    data: FewShotExampleUpdate,
    db: Session = Depends(get_db),
):
    """Update a few-shot example."""
    example = db.query(FewShotExample).filter(FewShotExample.id == example_id).first()
    if not example:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Example not found",
        )

    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(example, key, value)

    db.commit()
    db.refresh(example)
    return example


@router.delete("/{example_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_example(
    example_id: int,
    db: Session = Depends(get_db),
):
    """Delete a few-shot example."""
    example = db.query(FewShotExample).filter(FewShotExample.id == example_id).first()
    if not example:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Example not found",
        )

    db.delete(example)
    db.commit()
    return None
