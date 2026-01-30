'use client';

import { Upload, FileText, Sparkles, ArrowRight, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface EmptyStateProps {
  onUploadClick: () => void;
}

export function EmptyState({ onUploadClick }: EmptyStateProps) {
  const handleDownloadSample = () => {
    // Open the sample lease in a new tab
    window.open('/sample-lease.pdf', '_blank');
  };

  return (
    <div className="text-center py-16 px-4">
      {/* Icon */}
      <div className="mx-auto w-24 h-24 bg-gradient-to-br from-blue-100 to-purple-100 rounded-2xl flex items-center justify-center mb-8">
        <Sparkles className="w-12 h-12 text-blue-600" />
      </div>

      {/* Welcome Text */}
      <h2 className="text-3xl font-bold text-gray-900 mb-4">
        Welcome to LeaseBee! 🐝
      </h2>
      <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-8">
        AI-powered lease abstraction that extracts 40+ data points from commercial leases 
        in under 2 minutes. Save 70-90% of your review time.
      </p>

      {/* How it Works */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto mb-12">
        <div className="p-6 bg-white rounded-xl border border-gray-200 shadow-sm">
          <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4 mx-auto">
            <Upload className="w-6 h-6 text-blue-600" />
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">1. Upload PDF</h3>
          <p className="text-sm text-gray-600">
            Drag and drop your commercial lease or click to browse
          </p>
        </div>

        <div className="p-6 bg-white rounded-xl border border-gray-200 shadow-sm">
          <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4 mx-auto">
            <Sparkles className="w-6 h-6 text-purple-600" />
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">2. AI Extracts Data</h3>
          <p className="text-sm text-gray-600">
            Claude AI reads and extracts key terms, dates, and financials
          </p>
        </div>

        <div className="p-6 bg-white rounded-xl border border-gray-200 shadow-sm">
          <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4 mx-auto">
            <FileText className="w-6 h-6 text-green-600" />
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">3. Review & Export</h3>
          <p className="text-sm text-gray-600">
            Verify extractions and export to Excel or your system
          </p>
        </div>
      </div>

      {/* CTA Buttons */}
      <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
        <Button onClick={onUploadClick} size="lg" className="px-8">
          <Upload className="mr-2 h-5 w-5" />
          Upload Your First Lease
        </Button>
        
        <Button onClick={handleDownloadSample} variant="outline" size="lg">
          <Download className="mr-2 h-5 w-5" />
          Download Sample Lease
        </Button>
      </div>

      {/* Sample Lease Info */}
      <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-100 max-w-2xl mx-auto">
        <p className="text-sm text-blue-800">
          <strong>New to LeaseBee?</strong> Download our sample commercial lease to see 
          how the AI extracts parties, terms, rent, and 40+ other data points with 
          source citations.
        </p>
      </div>

      {/* Trust Indicators */}
      <div className="mt-12 flex flex-wrap justify-center gap-8 text-sm text-gray-500">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
          <span>100+ lease fields extracted</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
          <span>Bank-grade security</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
          <span>Human-in-the-loop review</span>
        </div>
      </div>
    </div>
  );
}
