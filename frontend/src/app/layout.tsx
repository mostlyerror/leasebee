import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });

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
          {children}
        </Providers>
      </body>
    </html>
  );
}
