'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
  getCurrentOrgId,
  setCurrentOrgId,
  isTokenExpired,
} from '@/lib/auth';

// Types
export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
  is_active: boolean;
  created_at: string;
}

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

export interface SignupData {
  email: string;
  password: string;
  name: string;
  organization_name?: string;
}

interface AuthContextType {
  user: User | null;
  organizations: OrganizationMembership[];
  currentOrg: Organization | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (data: SignupData) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  switchOrganization: (orgId: string) => void;
  refetchUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [organizations, setOrganizations] = useState<OrganizationMembership[]>([]);
  const [currentOrg, setCurrentOrg] = useState<Organization | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Fetch current user
  const fetchUser = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setIsLoading(false);
      return;
    }

    try {
      // Check if token needs refresh
      if (isTokenExpired(token)) {
        await refreshTokenFunc();
        return;
      }

      const response = await fetch(`${API_URL}/api/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          await refreshTokenFunc();
          return;
        }
        throw new Error('Failed to fetch user');
      }

      const userData = await response.json();
      setUser(userData);

      // Fetch organizations
      await fetchOrganizations(token);
    } catch (error) {
      console.error('Error fetching user:', error);
      clearTokens();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, [API_URL]);

  // Fetch user's organizations
  const fetchOrganizations = async (token?: string) => {
    const accessToken = token || getAccessToken();
    if (!accessToken) return;

    try {
      const response = await fetch(`${API_URL}/api/organizations`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) throw new Error('Failed to fetch organizations');

      const orgs = await response.json();
      setOrganizations(orgs);

      // Set current org
      const savedOrgId = getCurrentOrgId();
      if (savedOrgId && orgs.find((o: OrganizationMembership) => o.organization.id === savedOrgId)) {
        setCurrentOrg(orgs.find((o: OrganizationMembership) => o.organization.id === savedOrgId)?.organization || null);
      } else if (orgs.length > 0) {
        setCurrentOrg(orgs[0].organization);
        setCurrentOrgId(orgs[0].organization.id);
      }
    } catch (error) {
      console.error('Error fetching organizations:', error);
    }
  };

  // Refresh access token
  const refreshTokenFunc = async () => {
    const refresh = getRefreshToken();
    if (!refresh) {
      clearTokens();
      setUser(null);
      setIsLoading(false);
      return;
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
        throw new Error('Token refresh failed');
      }

      const data = await response.json();
      setTokens(data.access_token, data.refresh_token);

      // Retry fetching user
      await fetchUser();
    } catch (error) {
      console.error('Error refreshing token:', error);
      clearTokens();
      setUser(null);
      setIsLoading(false);
    }
  };

  // Login
  const login = async (email: string, password: string) => {
    try {
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

      const data = await response.json();
      setTokens(data.access_token, data.refresh_token);
      setUser(data.user);

      // Fetch organizations
      await fetchOrganizations(data.access_token);

      router.push('/');
    } catch (error) {
      throw error;
    }
  };

  // Signup
  const signup = async (signupData: SignupData) => {
    try {
      const response = await fetch(`${API_URL}/api/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(signupData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Signup failed');
      }

      const data = await response.json();
      setTokens(data.access_token, data.refresh_token);
      setUser(data.user);

      // Fetch organizations
      await fetchOrganizations(data.access_token);

      router.push('/');
    } catch (error) {
      throw error;
    }
  };

  // Logout
  const logout = () => {
    clearTokens();
    setUser(null);
    setOrganizations([]);
    setCurrentOrg(null);
    router.push('/login');
  };

  // Switch organization
  const switchOrganization = (orgId: string) => {
    const membership = organizations.find((o) => o.organization.id === orgId);
    if (membership) {
      setCurrentOrg(membership.organization);
      setCurrentOrgId(orgId);
      router.refresh();
    }
  };

  // Load user on mount
  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const value = {
    user,
    organizations,
    currentOrg,
    isAuthenticated: !!user,
    isLoading,
    login,
    signup,
    logout,
    refreshToken: refreshTokenFunc,
    switchOrganization,
    refetchUser: fetchUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
