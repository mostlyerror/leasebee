/**
 * TypeScript type definitions for the application.
 */

export enum LeaseStatus {
  UPLOADED = "uploaded",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed",
  REVIEWED = "reviewed",
}

export enum FieldCategory {
  BASIC_INFO = "basic_info",
  PARTIES = "parties",
  PROPERTY = "property",
  FINANCIAL = "financial",
  DATES_TERM = "dates_term",
  RENT = "rent",
  OPERATING_EXPENSES = "operating_expenses",
  RIGHTS_OPTIONS = "rights_options",
  USE_RESTRICTIONS = "use_restrictions",
  MAINTENANCE = "maintenance",
  INSURANCE = "insurance",
  OTHER = "other",
}

export enum FieldType {
  TEXT = "text",
  NUMBER = "number",
  DATE = "date",
  CURRENCY = "currency",
  BOOLEAN = "boolean",
  PERCENTAGE = "percentage",
  AREA = "area",
  ADDRESS = "address",
  LIST = "list",
}

export type LeaseStatusType = 'uploaded' | 'processing' | 'completed' | 'failed';

export interface Lease {
  id: number;
  filename: string;
  original_filename: string;
  file_size: number;
  status: LeaseStatusType;
  page_count?: number | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
  processed_at?: string | null;
}

export interface Extraction {
  id: number;
  lease_id: number;
  extractions: Record<string, any>;
  reasoning?: Record<string, string> | null;
  citations?: Record<string, Citation> | null;
  confidence?: Record<string, number> | null;
  model_version: string;
  prompt_version?: string;
  input_tokens?: number;
  output_tokens?: number;
  total_cost?: number;
  processing_time_seconds?: number;
  created_at: string;
}

export interface Citation {
  page: number;
  quote: string;
}

export interface FieldCorrection {
  id: number;
  extraction_id: number;
  field_path: string;
  original_value?: string;
  corrected_value?: string;
  correction_reason?: string;
  correction_category?: string;
  created_at: string;
}

export interface FieldDefinition {
  path: string;
  label: string;
  category: string;
  type: string;
  description: string;
  required: boolean;
}

export interface FieldSchema {
  fields: FieldDefinition[];
  categories: string[];
}

export interface ExportRequest {
  include_citations?: boolean;
  include_reasoning?: boolean;
  format?: string;
}

export interface ExportResponse {
  data: Record<string, any>;
  metadata: Record<string, any>;
}

export interface ApiError {
  detail: string;
}
