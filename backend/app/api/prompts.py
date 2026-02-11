"""Prompt template API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.prompt import PromptTemplate
from app.schemas.pydantic_schemas import (
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse,
)

router = APIRouter()


def _next_version(db: Session) -> str:
    """Generate the next version string (e.g., 1.1 -> 1.2)."""
    latest = (
        db.query(PromptTemplate)
        .order_by(PromptTemplate.id.desc())
        .first()
    )
    if not latest:
        return "1.1"
    try:
        parts = latest.version.split(".")
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        return f"{major}.{minor + 1}"
    except (ValueError, IndexError):
        return f"{latest.id + 1}.0"


@router.get("/", response_model=List[PromptTemplateResponse])
async def list_prompts(db: Session = Depends(get_db)):
    """List all prompt template versions."""
    return (
        db.query(PromptTemplate)
        .order_by(PromptTemplate.id.desc())
        .all()
    )


@router.get("/active", response_model=PromptTemplateResponse)
async def get_active_prompt(db: Session = Depends(get_db)):
    """Get the currently active prompt template."""
    prompt = (
        db.query(PromptTemplate)
        .filter(PromptTemplate.is_active == True)
        .first()
    )
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active prompt template found",
        )
    return prompt


@router.post("/", response_model=PromptTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    data: PromptTemplateCreate,
    db: Session = Depends(get_db),
):
    """Create a new prompt template version (inactive by default)."""
    version = _next_version(db)

    prompt = PromptTemplate(
        version=version,
        name=data.name,
        description=data.description,
        system_prompt=data.system_prompt,
        field_type_guidance=data.field_type_guidance,
        extraction_examples=data.extraction_examples,
        null_value_guidance=data.null_value_guidance,
        is_active=False,
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


@router.patch("/{prompt_id}", response_model=PromptTemplateResponse)
async def update_prompt(
    prompt_id: int,
    data: PromptTemplateUpdate,
    db: Session = Depends(get_db),
):
    """Update a prompt template's fields."""
    prompt = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found",
        )

    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prompt, key, value)

    db.commit()
    db.refresh(prompt)
    return prompt


@router.post("/{prompt_id}/activate", response_model=PromptTemplateResponse)
async def activate_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
):
    """Activate a prompt template (deactivates all others)."""
    prompt = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found",
        )

    # Deactivate all others
    db.query(PromptTemplate).filter(PromptTemplate.id != prompt_id).update(
        {"is_active": False}
    )

    # Activate this one
    prompt.is_active = True
    db.commit()
    db.refresh(prompt)
    return prompt


@router.post("/{prompt_id}/duplicate", response_model=PromptTemplateResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
):
    """Duplicate a prompt template for editing."""
    source = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found",
        )

    version = _next_version(db)

    new_prompt = PromptTemplate(
        version=version,
        name=f"{source.name} (copy)",
        description=source.description,
        system_prompt=source.system_prompt,
        field_type_guidance=source.field_type_guidance,
        extraction_examples=source.extraction_examples,
        null_value_guidance=source.null_value_guidance,
        is_active=False,
    )
    db.add(new_prompt)
    db.commit()
    db.refresh(new_prompt)
    return new_prompt
