import { Loader2, ChevronDown } from "lucide-react";

export function LoadingSpinner({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-gray-400 gap-3">
      <Loader2 className="w-8 h-8 animate-spin text-stadium-lime" />
      <span className="text-sm">{label}</span>
    </div>
  );
}

export function ErrorBox({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="glass-card p-6 border-l-4 border-stadium-rose text-center max-w-md mx-auto">
      <p className="text-stadium-rose font-semibold mb-2">⚠️ Error</p>
      <p className="text-gray-400 text-sm mb-4">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-stadium-lime/20 text-stadium-lime rounded-lg hover:bg-stadium-lime/30 transition-colors"
        >
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-gray-500 gap-2">
      <span className="text-4xl">🏟️</span>
      <p className="text-sm">{message}</p>
    </div>
  );
}

export function LoadMoreButton({
  onClick,
  loading,
  current,
  total,
}: {
  onClick: () => void;
  loading: boolean;
  current: number;
  total: number;
}) {
  return (
    <div className="flex flex-col items-center gap-2 pt-8 pb-4">
      <button
        onClick={onClick}
        disabled={loading}
        className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-6 py-3 text-sm font-medium text-gray-300 transition-all hover:bg-white/10 hover:text-white disabled:opacity-50"
      >
        {loading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <ChevronDown className="w-4 h-4" />
        )}
        {loading ? "Loading…" : "Load More"}
      </button>
      <span className="text-xs text-gray-600">
        Showing {current} of {total}
      </span>
    </div>
  );
}
