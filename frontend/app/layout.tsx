import type { Metadata } from 'next';
import { Libre_Baskerville, Source_Sans_3 } from 'next/font/google';
import './globals.css';
import { DisclaimerBanner } from '@/components/DisclaimerBanner';
import { Nav } from '@/components/Nav';
import { Footer } from '@/components/Footer';

const libreBaskerville = Libre_Baskerville({
  subsets: ['latin'],
  weight: ['400', '700'],
  variable: '--font-libre-baskerville',
  display: 'swap',
});

const sourceSans = Source_Sans_3({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  variable: '--font-source-sans',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'VetBuddy — Veteran Benefits Guidance',
  description:
    'Educational veteran benefits guidance. Alabama pilot with national 56-jurisdiction comparison. Not legal advice.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${libreBaskerville.variable} ${sourceSans.variable}`}>
      <body className="min-h-screen flex flex-col">
        <DisclaimerBanner />
        <Nav />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
