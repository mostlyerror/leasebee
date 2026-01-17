import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: '🐝 LeaseBee - Smart Lease Abstraction',
  description: 'AI-powered commercial lease abstraction. Buzzing through leases in seconds.',
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
          <div className="min-h-screen bg-gray-50">
            <nav className="bg-white shadow-sm border-b">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16 items-center">
                  <div className="flex items-center">
                    <span className="text-2xl mr-2">🐝</span>
                    <h1 className="text-xl font-bold text-gray-900">
                      LeaseBee
                    </h1>
                  </div>
                  <div className="flex items-center space-x-4">
                    <a
                      href="/"
                      className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                    >
                      Dashboard
                    </a>
                  </div>
                </div>
              </div>
            </nav>
            <main>{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
