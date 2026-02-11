"""Extraction API endpoints."""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.models.lease import Lease, LeaseStatus
from app.models.extraction import Extraction
from app.models.field_correction import FieldCorrection
from app.models.few_shot_example import FewShotExample
from app.models.prompt import PromptTemplate
from app.schemas.pydantic_schemas import (
    ExtractionResponse,
    ExtractionUpdate,
    FieldCorrectionCreate,
    FieldCorrectionResponse,
    ExportRequest,
    ExportResponse,
    FieldSchemaResponse,
    FieldDefinition,
)
from app.schemas.field_schema import LEASE_FIELDS, FieldCategory, get_field_by_path
from app.services.storage_service import storage_service
from app.services.claude_service import claude_service
from app.services.validation_service import validation_service
from app.services.pdf_service import pdf_service
from app.services.progress_tracker import create_tracker, get_tracker, remove_tracker, ExtractionStage

router = APIRouter()


async def cleanup_tracker_after_delay(operation_id: str, delay_seconds: int = 60):
    """Remove progress tracker after a delay to allow frontend to detect completion."""
    await asyncio.sleep(delay_seconds)
    remove_tracker(operation_id)


@router.post("/extract/{lease_id}", response_model=ExtractionResponse, status_code=status.HTTP_201_CREATED)
async def extract_lease_data(
    lease_id: int,
    background_tasks: BackgroundTasks,
    use_multi_pass: bool = True,
    db: Session = Depends(get_db)
):
    """
    Extract data from a lease PDF using Claude.

    Args:
        lease_id: Lease ID to extract
        background_tasks: FastAPI background tasks
        use_multi_pass: Enable multi-pass refinement for low-confidence fields (default: True)
        db: Database session

    Returns:
        Created extraction object

    Raises:
        HTTPException: If lease not found or extraction fails
    """
    # Create progress tracker using lease_id as operation_id
    operation_id = str(lease_id)
    tracker = create_tracker(operation_id)
    
    # Get lease
    lease = db.query(Lease).filter(Lease.id == lease_id).first()
    if not lease:
        remove_tracker(operation_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lease not found"
        )

    # Check if already processing
    if lease.status == LeaseStatus.PROCESSING:
        remove_tracker(operation_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lease is already being processed"
        )

    # Update status to processing
    lease.status = LeaseStatus.PROCESSING
    db.commit()

    try:
        # Stage: Extracting text from PDF
        tracker.advance_stage(ExtractionStage.EXTRACTING_TEXT)
        pdf_bytes = storage_service.download_pdf(lease.file_path)

        # Stage: AI Analyzing
        tracker.advance_stage(ExtractionStage.ANALYZING)

        # Load active few-shot examples for prompt enhancement
        few_shot_examples_db = (
            db.query(FewShotExample)
            .filter(FewShotExample.is_active == True)
            .order_by(FewShotExample.quality_score.desc().nullslast())
            .limit(30)
            .all()
        )
        few_shot_examples = None
        if few_shot_examples_db:
            few_shot_examples = [
                {
                    "field_path": ex.field_path,
                    "source_text": ex.source_text,
                    "correct_value": ex.correct_value,
                    "reasoning": ex.reasoning or "",
                }
                for ex in few_shot_examples_db
            ]
            # Increment usage_count on loaded examples
            for ex in few_shot_examples_db:
                ex.usage_count = (ex.usage_count or 0) + 1
            db.flush()

        # Load active prompt template (if one exists)
        active_prompt = (
            db.query(PromptTemplate)
            .filter(PromptTemplate.is_active == True)
            .first()
        )
        prompt_template_dict = None
        if active_prompt:
            prompt_template_dict = {
                "version": active_prompt.version,
                "system_prompt": active_prompt.system_prompt,
                "field_type_guidance": active_prompt.field_type_guidance,
                "extraction_examples": active_prompt.extraction_examples,
                "null_value_guidance": active_prompt.null_value_guidance,
            }
            active_prompt.usage_count = (active_prompt.usage_count or 0) + 1
            db.flush()

        # Extract data using Claude (with multi-pass if enabled)
        if use_multi_pass:
            result = claude_service.extract_lease_data_with_refinement(
                pdf_bytes,
                few_shot_examples=few_shot_examples,
                prompt_template=prompt_template_dict,
            )
        else:
            result = claude_service.extract_lease_data(
                pdf_bytes,
                few_shot_examples=few_shot_examples,
                prompt_template=prompt_template_dict,
            )

        # Stage: Parsing results
        tracker.advance_stage(ExtractionStage.PARSING)

        # Validate and normalize extracted values
        extractions_dict = result['extractions']
        reasoning_dict = result.get('reasoning', {})
        citations_dict = result.get('citations', {})
        confidence_dict = result.get('confidence', {})
        validation_warnings = {}

        # Enrich citations with bounding boxes
        if citations_dict:
            citations_dict = pdf_service.enrich_citations_with_bounding_boxes(
                pdf_bytes,
                citations_dict
            )

        for field_path, value in list(extractions_dict.items()):
            if value is not None:
                # Get field definition from schema
                field_def = get_field_by_path(field_path)

                if field_def:
                    # Validate and normalize
                    validation_result = validation_service.validate_and_normalize(
                        field_path,
                        value,
                        field_def['type'].value,
                        all_extractions=extractions_dict
                    )

                    # Update with normalized value
                    extractions_dict[field_path] = validation_result.value

                    # Adjust confidence if validation suggests issues
                    if validation_result.confidence_adjustment != 0:
                        current_confidence = confidence_dict.get(field_path, 0.5)
                        adjusted_confidence = max(
                            0.0,
                            min(1.0, current_confidence + validation_result.confidence_adjustment)
                        )
                        confidence_dict[field_path] = adjusted_confidence

                    # Store warnings
                    if validation_result.warnings:
                        validation_warnings[field_path] = validation_result.warnings

        # Add validation warnings and few-shot info to metadata
        if 'metadata' not in result:
            result['metadata'] = {}
        result['metadata']['validation_warnings'] = validation_warnings
        result['metadata']['few_shot_example_count'] = len(few_shot_examples) if few_shot_examples else 0
        
        # Stage: Validating
        tracker.advance_stage(ExtractionStage.VALIDATING)
        
        # Stage: Saving
        tracker.advance_stage(ExtractionStage.SAVING)

        # Create extraction record
        extraction = Extraction(
            lease_id=lease_id,
            extractions=extractions_dict,
            reasoning=reasoning_dict,
            citations=citations_dict,
            confidence=confidence_dict,
            model_version=result['metadata']['model_version'],
            prompt_version=result['metadata']['prompt_version'],
            input_tokens=result['metadata']['input_tokens'],
            output_tokens=result['metadata']['output_tokens'],
            total_cost=result['metadata']['total_cost'],
            processing_time_seconds=result['metadata']['processing_time_seconds'],
            extraction_metadata=result['metadata']
        )

        db.add(extraction)

        # Update lease status and confidence summary
        lease.status = LeaseStatus.COMPLETED
        lease.processed_at = datetime.utcnow()

        # Compute confidence summary from extracted confidence scores
        if confidence_dict:
            confidence_values = [v for v in confidence_dict.values() if isinstance(v, (int, float))]
            if confidence_values:
                lease.avg_confidence = round(sum(confidence_values) / len(confidence_values), 4)
                lease.min_confidence = round(min(confidence_values), 4)
                lease.low_confidence_count = sum(1 for v in confidence_values if v < 0.70)

        db.commit()
        db.refresh(extraction)
        
        # Complete progress tracking
        tracker.advance_stage(ExtractionStage.COMPLETE)
        remove_tracker(operation_id)

        # Complete progress tracking
        # Keep tracker alive for 60 seconds so frontend can detect completion
        tracker.advance_stage(ExtractionStage.COMPLETE)
        # Schedule tracker cleanup after 60 seconds
        background_tasks.add_task(cleanup_tracker_after_delay, operation_id, 60)

        return extraction

    except Exception as e:
        # Update lease status to failed
        lease.status = LeaseStatus.FAILED
        lease.error_message = str(e)
        db.commit()
        
        # Clean up progress tracker
        remove_tracker(operation_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failed: {str(e)}"
        )


@router.get("/lease/{lease_id}", response_model=List[ExtractionResponse])
async def get_lease_extractions(
    lease_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all extractions for a lease.

    Args:
        lease_id: Lease ID
        db: Database session

    Returns:
        List of extraction objects

    Raises:
        HTTPException: If lease not found
    """
    lease = db.query(Lease).filter(Lease.id == lease_id).first()
    if not lease:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lease not found"
        )

    extractions = db.query(Extraction).filter(
        Extraction.lease_id == lease_id
    ).order_by(Extraction.created_at.desc()).all()

    return extractions


@router.get("/{extraction_id}", response_model=ExtractionResponse)
async def get_extraction(
    extraction_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific extraction by ID.

    Args:
        extraction_id: Extraction ID
        db: Database session

    Returns:
        Extraction object

    Raises:
        HTTPException: If extraction not found
    """
    extraction = db.query(Extraction).filter(Extraction.id == extraction_id).first()
    if not extraction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found"
        )
    return extraction


@router.patch("/{extraction_id}", response_model=ExtractionResponse)
async def update_extraction(
    extraction_id: int,
    update_data: ExtractionUpdate,
    db: Session = Depends(get_db)
):
    """
    Update extraction data (after user review/editing).

    This endpoint is called when users make corrections to the extracted data.
    It updates the extraction and creates field correction records for learning.

    Args:
        extraction_id: Extraction ID
        update_data: Updated extraction data
        db: Database session

    Returns:
        Updated extraction object

    Raises:
        HTTPException: If extraction not found
    """
    extraction = db.query(Extraction).filter(Extraction.id == extraction_id).first()
    if not extraction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found"
        )

    # Track corrections
    original_extractions = extraction.extractions
    new_extractions = update_data.extractions

    # Find and record corrections
    for field_path, new_value in new_extractions.items():
        original_value = original_extractions.get(field_path)

        # Only create correction if value changed
        if original_value != new_value:
            correction = FieldCorrection(
                extraction_id=extraction_id,
                field_path=field_path,
                original_value=str(original_value) if original_value is not None else None,
                corrected_value=str(new_value) if new_value is not None else None,
                original_confidence=extraction.confidence.get(field_path) if extraction.confidence else None,
                original_reasoning=extraction.reasoning.get(field_path) if extraction.reasoning else None,
            )
            db.add(correction)

    # Update extraction
    extraction.extractions = new_extractions

    # Update lease status to reviewed
    extraction.lease.status = LeaseStatus.REVIEWED

    db.commit()
    db.refresh(extraction)

    return extraction


@router.post("/{extraction_id}/corrections", response_model=FieldCorrectionResponse)
async def create_field_correction(
    extraction_id: int,
    correction_data: FieldCorrectionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a field correction with user feedback.

    Args:
        extraction_id: Extraction ID
        correction_data: Correction data
        db: Database session

    Returns:
        Created field correction object

    Raises:
        HTTPException: If extraction not found
    """
    extraction = db.query(Extraction).filter(Extraction.id == extraction_id).first()
    if not extraction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found"
        )

    correction = FieldCorrection(
        extraction_id=extraction_id,
        **correction_data.dict()
    )

    db.add(correction)
    db.commit()
    db.refresh(correction)

    return correction


@router.get("/{extraction_id}/corrections", response_model=List[FieldCorrectionResponse])
async def get_extraction_corrections(
    extraction_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all corrections for an extraction.

    Args:
        extraction_id: Extraction ID
        db: Database session

    Returns:
        List of field correction objects
    """
    corrections = db.query(FieldCorrection).filter(
        FieldCorrection.extraction_id == extraction_id
    ).all()

    return corrections


@router.post("/{extraction_id}/export", response_model=ExportResponse)
async def export_extraction(
    extraction_id: int,
    export_request: ExportRequest,
    db: Session = Depends(get_db)
):
    """
    Export extraction data in specified format.

    Args:
        extraction_id: Extraction ID
        export_request: Export options
        db: Database session

    Returns:
        Exported data

    Raises:
        HTTPException: If extraction not found
    """
    extraction = db.query(Extraction).filter(Extraction.id == extraction_id).first()
    if not extraction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found"
        )

    # Build export data
    export_data = {
        "extractions": extraction.extractions,
    }

    if export_request.include_citations and extraction.citations:
        export_data["citations"] = extraction.citations

    if export_request.include_reasoning and extraction.reasoning:
        export_data["reasoning"] = extraction.reasoning

    # Add metadata
    metadata = {
        "lease_id": extraction.lease_id,
        "extraction_id": extraction.id,
        "lease_filename": extraction.lease.original_filename,
        "extracted_at": extraction.created_at.isoformat(),
        "model_version": extraction.model_version,
    }

    return ExportResponse(
        data=export_data,
        metadata=metadata
    )


@router.get("/schema/fields", response_model=FieldSchemaResponse)
async def get_field_schema():
    """
    Get the field schema definition.

    Returns:
        Field schema with all field definitions
    """
    fields = [
        FieldDefinition(
            path=f['path'],
            label=f['label'],
            category=f['category'].value,
            type=f['type'].value,
            description=f['description'],
            required=f.get('required', False)
        )
        for f in LEASE_FIELDS
    ]

    categories = list(set(f['category'].value for f in LEASE_FIELDS))

    return FieldSchemaResponse(
        fields=fields,
        categories=categories
    )


@router.get("/progress/{operation_id}")
async def get_extraction_progress(operation_id: str):
    """
    Get progress of an ongoing extraction operation.
    
    Args:
        operation_id: The operation ID (use lease_id as operation_id)
        
    Returns:
        Progress information including stage, percentage, and time estimates
    """
    tracker = get_tracker(operation_id)
    if not tracker:
        # If no tracker found, extraction might be complete or not started
        return {
            "operation_id": operation_id,
            "stage": "unknown",
            "stage_description": "Extraction status unknown",
            "percentage": 0,
            "elapsed_seconds": 0,
            "estimated_remaining_seconds": 0,
            "tip": "Waiting to start...",
            "completed_stages": [],
        }
    
    return tracker.get_progress()
