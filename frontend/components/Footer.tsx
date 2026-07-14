import Link from 'next/link';

export function Footer() {
  return (
    <footer className="border-t border-cream-300 bg-navy text-cream-100">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-8 md:grid-cols-4">
          <div className="md:col-span-1">
            <p className="font-display text-2xl font-bold text-cream">VetBuddy</p>
            <p className="mt-2 text-sm text-cream-200">
              Educational veteran benefits guidance. Alabama pilot, national reach across all 56
              jurisdictions.
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-cream">Resources</h4>
            <ul className="mt-3 space-y-2 text-sm">
              <li><Link href="/alabama" className="hover:text-sage-200">Alabama Center</Link></li>
              <li><Link href="/state-comparison" className="hover:text-sage-200">State Comparison</Link></li>
              <li><Link href="/benefits" className="hover:text-sage-200">Benefits Search</Link></li>
              <li><Link href="/claims/forms" className="hover:text-sage-200">VA Forms Guide</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-cream">Claims</h4>
            <ul className="mt-3 space-y-2 text-sm">
              <li><Link href="/claims" className="hover:text-sage-200">Claims Dashboard</Link></li>
              <li><Link href="/claims/intent-to-file" className="hover:text-sage-200">Intent to File</Link></li>
              <li><Link href="/claims/evidence" className="hover:text-sage-200">Evidence Checklist</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-cream">Account</h4>
            <ul className="mt-3 space-y-2 text-sm">
              <li><Link href="/register" className="hover:text-sage-200">Register</Link></li>
              <li><Link href="/login" className="hover:text-sage-200">Log in</Link></li>
              <li><Link href="/billing" className="hover:text-sage-200">Subscription</Link></li>
            </ul>
          </div>
        </div>
        <div className="mt-10 border-t border-navy-600 pt-6 text-center text-xs text-cream-300">
          <p>
            VetBuddy provides educational guidance and organization support only. This is not legal
            advice and does not constitute accredited VA representation. Always verify benefits with
            official VA, state veterans agencies, and accredited representatives.
          </p>
          <p className="mt-2">&copy; {new Date().getFullYear()} VetBuddy. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}
