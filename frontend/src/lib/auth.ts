/**
 * Authentication utilities for token management
 */

import { decodeJwt } from 'jose';

// Storage keys
const ACCESS_TOKEN_KEY = 'leasebee_access_token';
const REFRESH_TOKEN_KEY = 'leasebee_refresh_token';
const CURRENT_ORG_KEY = 'leasebee_current_org_id';

// Token utilities
export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(accessToken: string, refreshToken: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearTokens(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(CURRENT_ORG_KEY);
}

export function getCurrentOrgId(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(CURRENT_ORG_KEY);
}

export function setCurrentOrgId(orgId: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(CURRENT_ORG_KEY, orgId);
}

export function isTokenExpired(token: string): boolean {
  try {
    const decoded = decodeJwt(token);
    if (!decoded.exp) return true;

    // Check if token expires in less than 5 minutes
    const expiryTime = decoded.exp * 1000; // Convert to milliseconds
    const now = Date.now();
    const fiveMinutes = 5 * 60 * 1000;

    return expiryTime - now < fiveMinutes;
  } catch (error) {
    return true;
  }
}

export function decodeToken(token: string): any {
  try {
    return decodeJwt(token);
  } catch (error) {
    return null;
  }
}
