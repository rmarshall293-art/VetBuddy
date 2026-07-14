export function DisclaimerBanner() {
  return (
    <div className="bg-navy-800/95 text-cream-100">
      <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-2.5 text-xs sm:px-6 sm:text-sm">
        <svg
          className="h-4 w-4 shrink-0 text-gold-light"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <p>
          <strong className="font-semibold">Educational disclaimer:</strong> VetBuddy is not a law
          firm and does not provide legal advice or accredited VA representation. Content is for
          educational and organizational purposes only.
        </p>
      </div>
    </div>
  );
}
