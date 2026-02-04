'use client';

import { Upload, FileText, Sparkles, Download, ArrowRight, Clock, Shield, Zap, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

interface EmptyStateProps {
  onUploadClick: () => void;
  variant?: 'first-time' | 'all-caught-up';
}

export function EmptyState({ onUploadClick, variant = 'first-time' }: EmptyStateProps) {
  const handleDownloadSample = () => {
    window.open('/sample-lease.pdf', '_blank');
  };

  // All caught up variant (when user has leases but none need attention)
  if (variant === 'all-caught-up') {
    return (
      <div className="mt-12">
        <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-12 text-center border border-green-100">
          <div className="mx-auto w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mb-6">
            <CheckCircle className="w-10 h-10 text-green-600" />
          </div>

          <h2 className="text-3xl font-bold text-slate-900 mb-4">
            All Caught Up!
          </h2>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto mb-8">
            No leases need review right now. Upload a new lease or view your complete history.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              onClick={onUploadClick}
              size="lg"
              className="bg-amber-500 hover:bg-amber-600 text-white px-8 h-12 text-base font-semibold"
            >
              <Upload className="mr-2 h-5 w-5" />
              Upload New Lease
            </Button>
            <Link href="/history">
              <Button
                variant="outline"
                size="lg"
                className="border-slate-300 text-slate-700 hover:bg-slate-50 px-8 h-12 text-base w-full sm:w-auto"
              >
                <FileText className="mr-2 h-5 w-5" />
                View History
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // First time user variant
  const features = [
    { icon: Zap, text: 'Extract 40+ data points automatically' },
    { icon: Clock, text: 'Save 2+ hours per lease review' },
    { icon: Shield, text: 'Bank-grade security & privacy' },
  ];

  return (
    <div className="mt-12">
      {/* Hero Card */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl p-8 sm:p-12 text-center text-white shadow-xl">
        {/* Logo */}
        <div className="mx-auto w-20 h-20 bg-gradient-to-br from-amber-400 to-orange-500 rounded-2xl flex items-center justify-center mb-6 shadow-lg shadow-amber-500/25">
          <span className="text-4xl">🐝</span>
        </div>

        <h2 className="text-3xl sm:text-4xl font-bold mb-4">
          Welcome to LeaseBee
        </h2>
        <p className="text-lg text-slate-300 max-w-2xl mx-auto mb-8">
          AI-powered lease abstraction that extracts critical data from commercial leases
          in under 2 minutes. No more manual review marathons.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button
            onClick={onUploadClick}
            size="lg"
            className="bg-white text-slate-900 hover:bg-slate-100 px-8 h-12 text-base font-semibold"
          >
            <Upload className="mr-2 h-5 w-5" />
            Upload Your First Lease
          </Button>
          <Button
            onClick={handleDownloadSample}
            variant="outline"
            size="lg"
            className="border-slate-600 text-white hover:bg-slate-800 px-8 h-12 text-base"
          >
            <Download className="mr-2 h-5 w-5" />
            Download Sample
          </Button>
        </div>
      </div>

      {/* How it Works */}
      <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          {
            step: '01',
            title: 'Upload PDF',
            description: 'Drag and drop your commercial lease. We support all standard PDF formats.',
            icon: Upload,
            color: 'bg-blue-500',
          },
          {
            step: '02',
            title: 'AI Extraction',
            description: 'Claude AI reads and extracts parties, terms, rent, and 40+ data points.',
            icon: Sparkles,
            color: 'bg-purple-500',
          },
          {
            step: '03',
            title: 'Review & Export',
            description: 'Verify extractions with source citations, then export to Excel or your system.',
            icon: FileText,
            color: 'bg-green-500',
          },
        ].map((item) => (
          <div
            key={item.step}
            className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm hover:shadow-md transition-shadow"
          >
            <div className="flex items-center gap-4 mb-4">
              <div className={`${item.color} w-12 h-12 rounded-xl flex items-center justify-center`}>
                <item.icon className="w-6 h-6 text-white" />
              </div>
              <span className="text-3xl font-bold text-slate-200">{item.step}</span>
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">{item.title}</h3>
            <p className="text-slate-600 text-sm leading-relaxed">{item.description}</p>
          </div>
        ))}
      </div>

      {/* Features */}
      <div className="mt-12 flex flex-wrap justify-center gap-6">
        {features.map((feature) => (
          <div key={feature.text} className="flex items-center gap-2 text-slate-600">
            <feature.icon className="w-5 h-5 text-amber-500" />
            <span className="text-sm font-medium">{feature.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
