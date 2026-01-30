import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'LeaseBee - AI-Powered Lease Abstraction',
  description: 'Extract 40+ data points from commercial leases in under 2 minutes. Save 70-90% of review time with AI-powered abstraction.',
  keywords: 'lease abstraction, commercial real estate, AI, document extraction',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          <div className="min-h-screen bg-slate-50">
            {/* Navigation */}
            <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16 items-center">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-amber-400 to-orange-500 rounded-xl flex items-center justify-center shadow-sm">
                      <span className="text-xl">🐝</span>
                    </div>
                    <div>
                      <h1 className="text-xl font-bold bg-gradient-to-r from-slate-900 to-slate-600 bg-clip-text text-transparent">
                        LeaseBee
                      </h1>
                      <p className="text-xs text-slate-500 -mt-0.5">AI-Powered Lease Abstraction</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-1">
                    <a
                      href="/"
                      className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
                    >
                      Dashboard
                    </a>
                  </div>
                </div>
              </div>
            </nav>

            {/* Main Content */}
            <main>{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
