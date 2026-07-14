import Link from 'next/link';
import { Button } from '@/components/ui/Button';

export default function HomePage() {
  return (
    <div className="relative -mt-[calc(4rem+2.5rem)]">
      {/* Full-bleed hero */}
      <section className="relative min-h-screen bg-hero-gradient bg-mesh-pattern overflow-hidden">
        {/* Atmospheric orbs */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute -left-32 top-1/4 h-96 w-96 rounded-full bg-sage/20 blur-3xl animate-pulse-soft" />
          <div className="absolute -right-24 bottom-1/4 h-80 w-80 rounded-full bg-navy/10 blur-3xl animate-pulse-soft stagger-2" />
          <div className="absolute left-1/2 top-0 h-64 w-[600px] -translate-x-1/2 rounded-full bg-gold/5 blur-3xl" />
        </div>

        <div className="relative mx-auto flex min-h-screen max-w-7xl flex-col justify-center px-4 pt-32 pb-20 sm:px-6 lg:px-8 lg:flex-row lg:items-center lg:gap-16">
          {/* Copy column */}
          <div className="flex-1 lg:max-w-xl">
            <p className="opacity-0-start animate-fade-in-up stagger-1 mb-4 text-sm font-semibold uppercase tracking-widest text-sage-600">
              Alabama Pilot · 56 Jurisdictions
            </p>

            <h1 className="opacity-0-start animate-fade-in-up stagger-2 font-display text-6xl font-bold leading-[1.05] tracking-tight text-navy sm:text-7xl lg:text-8xl">
              VetBuddy
            </h1>

            <p className="opacity-0-start animate-fade-in-up stagger-3 mt-6 text-2xl font-display text-navy-600 sm:text-3xl text-balance">
              Navigate benefits with clarity — from Alabama to every state and territory.
            </p>

            <p className="opacity-0-start animate-fade-in-up stagger-4 mt-4 text-lg text-navy-500 max-w-md">
              Educational guidance for claims, evidence, and jurisdiction comparison. Built for
              veteran trust, not legal complexity.
            </p>

            <div className="opacity-0-start animate-fade-in-up stagger-4 mt-10 flex flex-wrap gap-4">
              <Link href="/register">
                <Button size="lg">Start Free</Button>
              </Link>
              <Link href="/state-comparison">
                <Button size="lg" variant="outline">
                  Compare Jurisdictions
                </Button>
              </Link>
              <Link href="/alabama">
                <Button size="lg" variant="ghost">
                  Alabama Resources →
                </Button>
              </Link>
            </div>
          </div>

          {/* Dominant visual plane — no cards */}
          <div className="mt-16 flex-1 lg:mt-0">
            <div className="relative mx-auto max-w-lg animate-float">
              <div className="hero-visual-plane relative aspect-square rounded-3xl border border-cream-300/60 shadow-2xl shadow-navy/10">
                {/* Decorative map grid */}
                <svg
                  className="absolute inset-0 h-full w-full rounded-3xl opacity-30"
                  viewBox="0 0 400 400"
                  fill="none"
                >
                  <defs>
                    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1a2744" strokeWidth="0.5" opacity="0.15" />
                    </pattern>
                  </defs>
                  <rect width="400" height="400" fill="url(#grid)" />
                  <circle cx="200" cy="200" r="120" stroke="#8fa68f" strokeWidth="1.5" opacity="0.4" />
                  <circle cx="200" cy="200" r="80" stroke="#1a2744" strokeWidth="1" opacity="0.3" />
                  <circle cx="200" cy="200" r="40" fill="#8fa68f" opacity="0.2" />
                  {/* Alabama highlight */}
                  <circle cx="248" cy="268" r="18" fill="#1a2744" opacity="0.7" />
                  <text x="248" y="272" textAnchor="middle" fill="white" fontSize="10" fontWeight="bold">AL</text>
                </svg>

                <div className="absolute inset-0 flex flex-col items-center justify-center p-8 text-center">
                  <p className="font-display text-5xl font-bold text-navy/80">56</p>
                  <p className="mt-1 text-sm font-semibold uppercase tracking-widest text-sage-600">
                    Jurisdictions
                  </p>
                  <div className="mt-6 grid grid-cols-3 gap-3 text-center text-xs text-navy-600">
                    <div>
                      <p className="font-display text-2xl font-bold text-navy">Claims</p>
                      <p>Evidence</p>
                    </div>
                    <div>
                      <p className="font-display text-2xl font-bold text-navy">Benefits</p>
                      <p>Search</p>
                    </div>
                    <div>
                      <p className="font-display text-2xl font-bold text-navy">States</p>
                      <p>Compare</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Floating accent elements */}
              <div className="absolute -right-4 top-8 rounded-xl bg-white/90 px-4 py-2 shadow-lg backdrop-blur-sm border border-sage/20 animate-fade-in stagger-3">
                <p className="text-xs font-medium text-sage-700">Alabama Pilot Active</p>
              </div>
              <div className="absolute -left-6 bottom-12 rounded-xl bg-navy px-4 py-2 shadow-lg animate-fade-in stagger-4">
                <p className="text-xs font-medium text-cream">Not legal advice</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features section — cards OK here for interaction */}
      <section className="border-t border-cream-300 bg-white/50 py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h2 className="font-display text-3xl font-bold text-navy text-center mb-12">
            Everything veterans need to get organized
          </h2>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                title: 'Claims Workspace',
                desc: 'Track disability claims, evidence strength, and intent-to-file dates in one place.',
                href: '/claims',
              },
              {
                title: '56-Jurisdiction Compare',
                desc: 'Side-by-side tax, housing, education, and healthcare metrics for any state or territory.',
                href: '/state-comparison',
              },
              {
                title: 'Alabama Resource Center',
                desc: 'Deep-dive Alabama benefits, county VSO offices, and resource officer training.',
                href: '/alabama',
              },
              {
                title: 'Benefits Search',
                desc: 'Search federal and state veteran benefits with eligibility guidance.',
                href: '/benefits',
              },
              {
                title: 'VA Forms Guide',
                desc: 'Educational overview of key VA forms including 21-526EZ and 21-0966.',
                href: '/claims/forms',
              },
              {
                title: 'Evidence Checklist',
                desc: 'Organize medical records, buddy statements, and nexus evidence.',
                href: '/claims/evidence',
              },
            ].map((feature) => (
              <Link
                key={feature.href}
                href={feature.href}
                className="group rounded-xl border border-cream-300 bg-cream/50 p-6 transition-all hover:border-sage hover:shadow-md"
              >
                <h3 className="font-display text-xl font-bold text-navy group-hover:text-sage-700">
                  {feature.title}
                </h3>
                <p className="mt-2 text-navy-500">{feature.desc}</p>
                <span className="mt-4 inline-block text-sm font-semibold text-sage-600 group-hover:translate-x-1 transition-transform">
                  Explore →
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* CTA band */}
      <section className="bg-navy py-16">
        <div className="mx-auto max-w-3xl px-4 text-center sm:px-6">
          <h2 className="font-display text-3xl font-bold text-cream">
            Ready to organize your benefits journey?
          </h2>
          <p className="mt-4 text-cream-200">
            $5.99/month for full access. Alabama veterans start here — compare anywhere nationwide.
          </p>
          <div className="mt-8 flex justify-center gap-4">
            <Link href="/register">
              <Button size="lg" variant="secondary">
                Create Account
              </Button>
            </Link>
            <Link href="/billing">
              <Button size="lg" variant="outline" className="border-cream text-cream hover:bg-cream hover:text-navy">
                View Pricing
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
