"""Pydantic schemas for API request/response validation."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# Lease schemas
class LeaseCreate(BaseModel):
    """Schema for creating a lease."""
    pass  # File upload handled separately


class LeaseResponse(BaseModel):
    """Schema for lease response."""
    id: int
    filename: str
    original_filename: str
    file_size: int
    status: str
    page_count: Optional[int] = None
    error_message: Optional[str] = None
    avg_confidence: Optional[float] = None
    low_confidence_count: Optional[int] = None
    min_confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Extraction schemas
class ExtractionResponse(BaseModel):
    """Schema for extraction response."""
    id: int
    lease_id: int
    extractions: Dict[str, Any]
    reasoning: Optional[Dict[str, Any]] = None
    citations: Optional[Dict[str, Any]] = None
    confidence: Optional[Dict[str, Any]] = None
    model_version: str
    prompt_version: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_cost: Optional[float] = None
    processing_time_seconds: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ExtractionUpdate(BaseModel):
    """Schema for updating extraction data."""
    extractions: Dict[str, Any]


class FieldCorrectionCreate(BaseModel):
    """Schema for creating a field correction."""
    field_path: str
    original_value: Optional[str] = None
    corrected_value: Optional[str] = None
    correction_type: Optional[str] = None  # 'accept', 'reject', or 'edit'
    notes: Optional[str] = None
    correction_reason: Optional[str] = None  # legacy
    correction_category: Optional[str] = None  # legacy


class FieldCorrectionResponse(BaseModel):
    """Schema for field correction response."""
    id: int
    extraction_id: int
    field_path: str
    original_value: Optional[str] = None
    corrected_value: Optional[str] = None
    correction_type: Optional[str] = None
    notes: Optional[str] = None
    correction_reason: Optional[str] = None
    correction_category: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Export schemas
class ExportRequest(BaseModel):
    """Schema for export request."""
    include_citations: bool = Field(default=False, description="Include citation data in export")
    include_reasoning: bool = Field(default=False, description="Include reasoning in export")
    format: str = Field(default="json", description="Export format (json, csv)")


class ExportResponse(BaseModel):
    """Schema for export response."""
    data: Dict[str, Any]
    metadata: Dict[str, Any]


# Field schema response
class FieldDefinition(BaseModel):
    """Schema for field definition."""
    path: str
    label: str
    category: str
    type: str
    description: str
    required: bool


class FieldSchemaResponse(BaseModel):
    """Schema for field schema response."""
    fields: List[FieldDefinition]
    categories: List[str]


# Few-shot example schemas
class FewShotExampleCreate(BaseModel):
    """Schema for creating a few-shot example."""
    field_path: str
    source_text: str
    correct_value: str
    reasoning: Optional[str] = None
    quality_score: Optional[float] = None

class FewShotExampleUpdate(BaseModel):
    """Schema for updating a few-shot example."""
    field_path: Optional[str] = None
    source_text: Optional[str] = None
    correct_value: Optional[str] = None
    reasoning: Optional[str] = None
    quality_score: Optional[float] = None
    is_active: Optional[bool] = None

class FewShotExampleResponse(BaseModel):
    """Schema for few-shot example response."""
    id: int
    field_path: str
    source_text: str
    correct_value: str
    reasoning: Optional[str] = None
    quality_score: Optional[float] = None
    usage_count: int
    is_active: bool
    created_at: datetime
    created_from_correction_id: Optional[int] = None

    class Config:
        from_attributes = True


# Prompt template schemas
class PromptTemplateCreate(BaseModel):
    """Schema for creating a prompt template."""
    name: str
    description: Optional[str] = None
    system_prompt: str
    field_type_guidance: str
    extraction_examples: str
    null_value_guidance: str

class PromptTemplateUpdate(BaseModel):
    """Schema for updating a prompt template."""
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    field_type_guidance: Optional[str] = None
    extraction_examples: Optional[str] = None
    null_value_guidance: Optional[str] = None

class PromptTemplateResponse(BaseModel):
    """Schema for prompt template response."""
    id: int
    version: str
    name: str
    description: Optional[str] = None
    system_prompt: str
    field_type_guidance: str
    extraction_examples: str
    null_value_guidance: str
    is_active: bool
    created_at: datetime
    usage_count: int
    avg_confidence: Optional[float] = None

    class Config:
        from_attributes = True
