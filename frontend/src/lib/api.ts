/**
 * API client for LeaseBee backend
 */

import { getAccessToken, getRefreshToken, setTokens, clearTokens, isTokenExpired } from './auth';
import type { Lease } from '../types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types

export interface Organization {
  id: string;
  name: string;
  slug: string;
  plan: string;
  created_at: string;
}

export interface OrganizationMembership {
  organization: Organization;
  role: 'ADMIN' | 'MEMBER' | 'VIEWER';
  joined_at: string;
}

export interface UserWithTokenResponse {
  user: User;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Extending types from shared definitions
export interface LeaseWithOrg extends Lease {
  organization_id?: string;
}

export interface FieldSchema {
  fields: FieldDefinition[];
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

// Refresh token helper
let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    const refresh = getRefreshToken();
    if (!refresh) {
      clearTokens();
      throw new Error('No refresh token available');
    }

    try {
      const response = await fetch(`${API_URL}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refresh }),
      });

      if (!response.ok) {
        clearTokens();
        throw new Error('Token refresh failed');
      }

      const data = await response.json();
      setTokens(data.access_token, data.refresh_token);
      return data.access_token;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

// Base fetch function with auth
async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  let token = getAccessToken();

  // Check if token needs refresh
  if (token && isTokenExpired(token)) {
    token = await refreshAccessToken();
  }

  const url = `${API_URL}${endpoint}`;
  const headers = new Headers(options?.headers);

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  let response = await fetch(url, {
    ...options,
    headers,
  });

  // Handle 401 by refreshing token and retrying
  if (response.status === 401 && token) {
    try {
      token = await refreshAccessToken();
      headers.set('Authorization', `Bearer ${token}`);

      response = await fetch(url, {
        ...options,
        headers,
      });
    } catch (error) {
      clearTokens();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
      throw error;
    }
  }

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`API Error: ${response.status} - ${error}`);
  }

  return response.json();
}

// Auth API
export const authApi = {
  async signup(data: {
    email: string;
    password: string;
    name: string;
    organization_name?: string;
  }): Promise<UserWithTokenResponse> {
    const response = await fetch(`${API_URL}/api/auth/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Signup failed');
    }

    return response.json();
  },

  async login(email: string, password: string): Promise<UserWithTokenResponse> {
    const response = await fetch(`${API_URL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    return response.json();
  },

  async me(): Promise<User> {
    return fetchApi('/api/auth/me');
  },

  async refresh(refreshToken: string): Promise<TokenResponse> {
    const response = await fetch(`${API_URL}/api/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      throw new Error('Token refresh failed');
    }

    return response.json();
  },

  logout(): void {
    clearTokens();
  },
};

// Organization API
export const organizationApi = {
  async list(): Promise<OrganizationMembership[]> {
    return fetchApi('/api/organizations');
  },

  async get(id: string): Promise<Organization> {
    return fetchApi(`/api/organizations/${id}`);
  },

  async create(data: { name: string }): Promise<Organization> {
    return fetchApi('/api/organizations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },
};

// Lease API
export const leaseApi = {
  async list(organizationId?: string): Promise<Lease[]> {
    const params = organizationId ? `?organization_id=${organizationId}` : '';
    return fetchApi(`/api/leases/${params}`);
  },

  async get(id: number): Promise<Lease> {
    return fetchApi(`/api/leases/${id}`);
  },

  async upload(file: File, organizationId?: string): Promise<Lease> {
    let token = getAccessToken();

    if (token && isTokenExpired(token)) {
      token = await refreshAccessToken();
    }

    const formData = new FormData();
    formData.append('file', file);

    const url = organizationId
      ? `${API_URL}/api/leases/upload?organization_id=${organizationId}`
      : `${API_URL}/api/leases/upload`;

    const headers = new Headers();
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }

    let response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    });

    // Handle 401 by refreshing token and retrying
    if (response.status === 401 && token) {
      try {
        token = await refreshAccessToken();
        headers.set('Authorization', `Bearer ${token}`);

        response = await fetch(url, {
          method: 'POST',
          headers,
          body: formData,
        });
      } catch (error) {
        clearTokens();
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        throw error;
      }
    }

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Upload failed: ${error}`);
    }

    return response.json();
  },

  async delete(id: number): Promise<void> {
    await fetchApi(`/api/leases/${id}`, {
      method: 'DELETE',
    });
  },

  getPdfUrl(id: number): string {
    const token = getAccessToken();
    return token
      ? `${API_URL}/api/leases/${id}/pdf?token=${token}`
      : `${API_URL}/api/leases/${id}/pdf`;
  },
};

// Extraction API
export const extractionApi = {
  async extract(leaseId: number): Promise<TypeExtraction> {
    return fetchApi(`/api/extractions/extract/${leaseId}`, {
      method: 'POST',
    });
  },

  async getByLease(leaseId: number): Promise<TypeExtraction[]> {
    return fetchApi(`/api/extractions/lease/${leaseId}`);
  },

  async get(id: number): Promise<TypeExtraction> {
    return fetchApi(`/api/extractions/${id}`);
  },

  async update(id: number, extractions: Record<string, any>): Promise<TypeExtraction> {
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
