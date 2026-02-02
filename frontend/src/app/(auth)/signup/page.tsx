'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export default function SignupPage() {
  const { signup } = useAuth();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    organizationName: '',
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [agreedToTerms, setAgreedToTerms] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const getPasswordStrength = (password: string): {
    strength: number;
    label: string;
    color: string;
  } => {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;

    if (strength <= 2) return { strength, label: 'Weak', color: 'bg-red-500' };
    if (strength <= 3) return { strength, label: 'Fair', color: 'bg-orange-500' };
    if (strength <= 4) return { strength, label: 'Good', color: 'bg-amber-500' };
    return { strength, label: 'Strong', color: 'bg-green-500' };
  };

  const passwordStrength = formData.password ? getPasswordStrength(formData.password) : null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    // Validation
    if (!formData.name || !formData.email || !formData.password) {
      setError('Please fill in all required fields');
      setIsLoading(false);
      return;
    }

    if (!formData.email.includes('@')) {
      setError('Please enter a valid email address');
      setIsLoading(false);
      return;
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters');
      setIsLoading(false);
      return;
    }

    if (!agreedToTerms) {
      setError('Please agree to the terms and conditions');
      setIsLoading(false);
      return;
    }

    try {
      await signup({
        name: formData.name,
        email: formData.email,
        password: formData.password,
        organization_name: formData.organizationName || undefined,
      });
    } catch (err: any) {
      setError(err.message || 'Signup failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">Create your account</h2>
        <p className="text-slate-600">Get started with LeaseBee today</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div>
          <label htmlFor="name" className="block text-sm font-medium text-slate-700 mb-1.5">
            Full name
          </label>
          <Input
            id="name"
            name="name"
            type="text"
            value={formData.name}
            onChange={handleChange}
            placeholder="John Doe"
            disabled={isLoading}
            required
          />
        </div>

        <div>
          <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-1.5">
            Email address
          </label>
          <Input
            id="email"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="you@company.com"
            disabled={isLoading}
            required
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium text-slate-700 mb-1.5">
            Password
          </label>
          <Input
            id="password"
            name="password"
            type="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="••••••••"
            disabled={isLoading}
            required
          />
          {passwordStrength && (
            <div className="mt-2">
              <div className="flex items-center gap-2">
                <div className="flex-1 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all ${passwordStrength.color}`}
                    style={{ width: `${(passwordStrength.strength / 5) * 100}%` }}
                  />
                </div>
                <span className="text-xs font-medium text-slate-600">
                  {passwordStrength.label}
                </span>
              </div>
            </div>
          )}
        </div>

        <div>
          <label htmlFor="organizationName" className="block text-sm font-medium text-slate-700 mb-1.5">
            Organization name <span className="text-slate-500 font-normal">(recommended)</span>
          </label>
          <Input
            id="organizationName"
            name="organizationName"
            type="text"
            value={formData.organizationName}
            onChange={handleChange}
            placeholder="ACME Corp"
            disabled={isLoading}
          />
          <p className="text-xs text-slate-500 mt-1">
            Create your organization now to start uploading leases immediately
          </p>
        </div>

        <div className="flex items-start gap-2">
          <input
            type="checkbox"
            id="terms"
            checked={agreedToTerms}
            onChange={(e) => setAgreedToTerms(e.target.checked)}
            className="w-4 h-4 mt-0.5 rounded border-slate-300 text-amber-500 focus:ring-amber-500"
            required
          />
          <label htmlFor="terms" className="text-sm text-slate-600">
            I agree to the{' '}
            <Link href="/terms" className="text-amber-600 hover:text-amber-700">
              Terms of Service
            </Link>{' '}
            and{' '}
            <Link href="/privacy" className="text-amber-600 hover:text-amber-700">
              Privacy Policy
            </Link>
          </label>
        </div>

        <Button
          type="submit"
          variant="primary"
          className="w-full"
          disabled={isLoading}
        >
          {isLoading ? 'Creating account...' : 'Create account'}
        </Button>
      </form>

      <div className="mt-6 text-center">
        <p className="text-sm text-slate-600">
          Already have an account?{' '}
          <Link
            href="/login"
            className="text-amber-600 hover:text-amber-700 font-medium"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
