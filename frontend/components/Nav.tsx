'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';
import { isAuthenticated } from '@/lib/auth';
import { Button } from './ui/Button';

const links = [
  { href: '/alabama', label: 'Alabama' },
  { href: '/state-comparison', label: 'Compare States' },
  { href: '/claims', label: 'Claims' },
  { href: '/benefits', label: 'Benefits' },
  { href: '/billing', label: 'Pricing' },
];

export function Nav() {
  const pathname = usePathname();
  const [authed, setAuthed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    setAuthed(isAuthenticated());
  }, [pathname]);

  const isLanding = pathname === '/';

  return (
    <header
      className={cn(
        'sticky top-0 z-50 w-full transition-all duration-300',
        isLanding
          ? 'bg-transparent'
          : 'border-b border-cream-300/60 bg-cream/90 backdrop-blur-md',
      )}
    >
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <Link href="/" className="group flex items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-navy text-cream font-display text-lg font-bold transition-transform group-hover:scale-105">
            V
          </span>
          <span
            className={cn(
              'font-display text-xl font-bold tracking-tight',
              isLanding ? 'text-navy' : 'text-navy',
            )}
          >
            VetBuddy
          </span>
        </Link>

        <div className="hidden items-center gap-1 md:flex">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                'rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                pathname.startsWith(link.href)
                  ? 'bg-sage/15 text-sage-700'
                  : 'text-navy-600 hover:bg-navy-50 hover:text-navy',
              )}
            >
              {link.label}
            </Link>
          ))}
        </div>

        <div className="hidden items-center gap-3 md:flex">
          {authed ? (
            <>
              <Link
                href="/dashboard"
                className="text-sm font-medium text-navy-600 hover:text-navy"
              >
                Dashboard
              </Link>
              <Link href="/claims">
                <Button size="sm" variant="primary">
                  My Claims
                </Button>
              </Link>
            </>
          ) : (
            <>
              <Link href="/login" className="text-sm font-medium text-navy-600 hover:text-navy">
                Log in
              </Link>
              <Link href="/register">
                <Button size="sm" variant="primary">
                  Get Started
                </Button>
              </Link>
            </>
          )}
        </div>

        <button
          className="md:hidden rounded-lg p-2 text-navy"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle menu"
        >
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            {mobileOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </nav>

      {mobileOpen && (
        <div className="border-t border-cream-300 bg-cream/95 px-4 py-4 md:hidden">
          <div className="flex flex-col gap-2">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className="rounded-lg px-3 py-2 text-navy-700 hover:bg-navy-50"
              >
                {link.label}
              </Link>
            ))}
            <hr className="my-2 border-cream-300" />
            {authed ? (
              <Link href="/dashboard" onClick={() => setMobileOpen(false)} className="px-3 py-2">
                Dashboard
              </Link>
            ) : (
              <>
                <Link href="/login" onClick={() => setMobileOpen(false)} className="px-3 py-2">
                  Log in
                </Link>
                <Link href="/register" onClick={() => setMobileOpen(false)}>
                  <Button className="w-full">Get Started</Button>
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
