export default function LoadingState() {
  return (
    <div className="space-y-3">
      <p className="text-sm text-zinc-500">
        Reasoning over the shortlist — checking each trial against the profile, criterion by
        criterion. This can take up to a minute.
      </p>
      {[0, 1, 2].map((i) => (
        <div key={i} className="animate-pulse rounded-lg border border-zinc-200 bg-white p-4">
          <div className="flex items-center justify-between gap-3">
            <div className="h-4 w-2/3 rounded bg-zinc-200" />
            <div className="h-5 w-24 rounded-full bg-zinc-200" />
          </div>
          <div className="mt-3 h-3 w-1/3 rounded bg-zinc-100" />
        </div>
      ))}
    </div>
  );
}
