import { Loader2 } from "lucide-react";

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
