function SkeletonBlock({ className }: { className?: string }) {
  return (
    <div className={`bg-neutral-900 rounded animate-pulse ${className ?? ""}`} />
  );
}

export default function ReportLoading() {
  return (
    <main className="max-w-[860px] mx-auto px-6 py-20">
      {/* Hero */}
      <div className="mb-16">
        <SkeletonBlock className="h-3 w-32 mb-6" />
        <SkeletonBlock className="h-12 w-3/4 mb-3" />
        <SkeletonBlock className="h-4 w-56 mb-10" />
        <div className="flex gap-8 py-6 border-t border-b border-neutral-900">
          {[...Array(4)].map((_, i) => (
            <div key={i}>
              <SkeletonBlock className="h-7 w-16 mb-2" />
              <SkeletonBlock className="h-3 w-12" />
            </div>
          ))}
        </div>
      </div>

      {/* Section */}
      <SkeletonBlock className="h-3 w-24 mb-8" />
      <div className="space-y-4 mb-20">
        <SkeletonBlock className="h-4 w-full" />
        <SkeletonBlock className="h-4 w-5/6" />
        <SkeletonBlock className="h-4 w-full" />
        <SkeletonBlock className="h-4 w-4/5" />
      </div>

      {/* Cards */}
      <SkeletonBlock className="h-3 w-20 mb-8" />
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="border border-neutral-800/50 rounded-xl p-6">
            <SkeletonBlock className="h-3 w-16 mb-3" />
            <SkeletonBlock className="h-5 w-3/4 mb-4" />
            <SkeletonBlock className="h-3 w-full mb-2" />
            <SkeletonBlock className="h-3 w-5/6" />
          </div>
        ))}
      </div>
    </main>
  );
}
