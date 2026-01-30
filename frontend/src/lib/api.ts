/**
 * API client for LeaseBee backend
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types
export interface Lease {
  id: number;
  filename: string;
  original_filename: string;
  file_size: number;
  status: 'uploaded' | 'processing' | 'completed' | 'failed';
  page_count: number | null;
  created_at: string;
  updated_at: string;
}

export interface Extraction {
  id: number;
  lease_id: number;
  extractions: Record<string, any>;
  reasoning: Record<string, string> | null;
  citations: Record<string, { page: number; quote: string }> | null;
  confidence: Record<string, number> | null;
  model_version: string;
  created_at: string;
}

export interface FieldSchema {
  fields: Array<{
    path: string;
    label: string;
    category: string;
    type: string;
    description: string;
    required: boolean;
  }>;
}

// Error handler
export function handleApiError(error: any): string {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  return 'An unknown error occurred';
}

// Base fetch function
async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      ...(options?.headers || {}),
    },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`API Error: ${response.status} - ${error}`);
  }

  return response.json();
}

// Lease API
export const leaseApi = {
  async list(): Promise<Lease[]> {
    return fetchApi('/api/leases/');
  },

  async get(id: number): Promise<Lease> {
    return fetchApi(`/api/leases/${id}`);
  },

  async upload(file: File): Promise<Lease> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_URL}/api/leases/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Upload failed: ${error}`);
    }

    return response.json();
  },

  async delete(id: number): Promise<void> {
    const response = await fetch(`${API_URL}/api/leases/${id}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to delete lease');
    }
  },
};

// Extraction API
export const extractionApi = {
  async extract(leaseId: number): Promise<Extraction> {
    return fetchApi(`/api/extractions/extract/${leaseId}`, {
      method: 'POST',
    });
  },

  async getByLease(leaseId: number): Promise<Extraction[]> {
    return fetchApi(`/api/extractions/lease/${leaseId}`);
  },

  async get(id: number): Promise<Extraction> {
    return fetchApi(`/api/extractions/${id}`);
  },

  async update(id: number, extractions: Record<string, any>): Promise<Extraction> {
    return fetchApi(`/api/extractions/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ extractions }),
    });
  },

  async export(id: number, options?: { include_citations?: boolean; include_reasoning?: boolean }): Promise<any> {
    return fetchApi(`/api/extractions/${id}/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(options || {}),
    });
  },

  async getFieldSchema(): Promise<FieldSchema> {
    return fetchApi('/api/extractions/schema/fields');
  },

  async submitCorrection(extractionId: number, correction: {
    field_path: string;
    original_value: any;
    corrected_value: any;
    correction_type: 'accept' | 'reject' | 'edit';
    notes?: string;
  }): Promise<any> {
    return fetchApi(`/api/extractions/${extractionId}/corrections`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(correction),
    });
  },
};
