import { useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowUp,
  ArrowDown,
  MessageCircle,
  Eye,
  Flame,
  Clock,
  TrendingUp,
  CalendarClock,
  ArrowUpNarrowWide,
  ArrowDownNarrowWide,
} from "lucide-react";
import { timeAgo } from "../utils/time";
import { usePaginatedApi } from "../hooks/usePaginatedApi";
import { threadsApi, type ThreadItem } from "../services/api";
import { stripMarkdown } from "../utils/markdown";
import {
  LoadingSpinner,
  ErrorBox,
  EmptyState,
  LoadMoreButton,
} from "../components/StatusStates";

function ThreadCard({
  thread,
  onVote,
}: {
  thread: ThreadItem;
  onVote: (id: number, dir: "up" | "down") => void;
}) {
  return (
    <div className="glass-card group overflow-hidden p-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div
          className="flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-gradient-to-br from-sky-400/[0.18] to-violet-300/[0.16]"
        >
          <span className="text-lg">{thread.league?.icon || "⚽"}</span>
        </div>
        <div className="flex-1 min-w-0">
          <span className="text-[11px] font-bold uppercase tracking-[0.24em] text-sky-300">
            {thread.league?.name ?? "General"}
          </span>
          <p className="mt-1 text-xs text-gray-500">
            by {thread.author.name}
            {thread.author.avatar_emoji && (
              <span className="ml-1">{thread.author.avatar_emoji}</span>
            )}
          </p>
        </div>
        {thread.karma > 50 && <span className="tag tag-hot">🔥 Hot</span>}
      </div>

      {/* Title — clickable */}
      <Link to={`/playground/thread/${thread.id}`}>
        <h3
          className="mb-3 line-clamp-2 cursor-pointer text-[1.35rem] font-black leading-tight text-white transition-colors group-hover:text-sky-300"
        >
          {thread.title}
        </h3>
      </Link>

      {/* Content preview — clickable */}
      <Link to={`/playground/thread/${thread.id}`}>
        <p className="mb-5 line-clamp-3 text-sm leading-7 text-gray-400 transition-colors cursor-pointer hover:text-gray-300">
          {stripMarkdown(thread.content)}
        </p>
      </Link>

      {/* Actions */}
      <div className="flex items-center gap-4 border-t border-white/[0.06] pt-4">
        <div className="flex items-center gap-1 rounded-full border border-sky-400/18 bg-sky-400/8 px-2 py-1">
          <button
            onClick={() => onVote(thread.id, "up")}
            className="rounded-full p-1.5 transition-colors hover:bg-sky-500/20"
          >
            <ArrowUp className="w-4 h-4 text-sky-300" />
          </button>
          <span className="min-w-[2rem] text-center text-sm font-bold text-sky-300">
            {thread.karma}
          </span>
          <button
            onClick={() => onVote(thread.id, "down")}
            className="rounded-full p-1.5 transition-colors hover:bg-rose-500/20"
          >
            <ArrowDown className="w-4 h-4 text-gray-500 hover:text-rose-400" />
          </button>
        </div>

        <Link
          to={`/playground/thread/${thread.id}`}
          className="flex items-center gap-1.5 text-sm text-gray-500 transition-colors hover:text-sky-300"
        >
          <MessageCircle className="w-4 h-4" />
          <span>{thread.comment_count ?? 0}</span>
        </Link>
        <div className="flex items-center gap-1.5 text-gray-500 text-sm">
          <Eye className="w-4 h-4" />
          <span>{thread.views}</span>
        </div>

        <span className="ml-auto flex items-center gap-1.5 text-xs text-gray-500">
          <Clock className="w-3.5 h-3.5" />
          {timeAgo(thread.created_at)}
        </span>
      </div>
    </div>
  );
}

export function Home() {
  const [sortBy, setSortBy] = useState<"hot" | "new" | "created_at" | "top">("new");
  const [dateOrder, setDateOrder] = useState<"desc" | "asc">("desc");
  const {
    items: threads,
    loading,
    error,
    refetch,
    hasMore,
    loadMore,
    loadingMore,
    total,
  } = usePaginatedApi(
    (page) => threadsApi.list(undefined, sortBy, page, 20, sortBy === "created_at" ? dateOrder : "desc"),
    [sortBy, dateOrder],
  );

  const handleVote = async (id: number, direction: "up" | "down") => {
    await threadsApi.vote(id, direction);
    refetch();
  };

  const sortIcons = {
    hot: <Flame className="w-4 h-4" />,
    new: <Clock className="w-4 h-4" />,
    created_at: <CalendarClock className="w-4 h-4" />,
    top: <TrendingUp className="w-4 h-4" />,
  };

  const sortLabels: Record<string, string> = {
    hot: "Hot",
    new: "New",
    created_at: "Created At",
    top: "Top",
  };

  return (
    <div>
      <div className="page-head">
        <div className="page-title-wrap">
          <p className="page-kicker">Main feed</p>
          <h1 className="page-title">Hot takes</h1>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="poster-metric min-w-[8rem] w-full sm:w-auto">
            <span className="poster-metric-label">Sort</span>
            <strong className="poster-metric-value text-white">
              {sortLabels[sortBy]}{sortBy === "created_at" ? ` (${dateOrder === "desc" ? "newest" : "oldest"})` : ""}
            </strong>
          </div>

          <div className="flex w-full flex-col items-stretch gap-3 sm:w-auto sm:flex-row sm:items-center">
            {/* Sort tabs */}
            <div className="flex max-w-full overflow-x-auto rounded-full border border-white/[0.06] bg-white/5 p-1 no-scrollbar">
              {(["hot", "new", "created_at", "top"] as const).map((s) => (
                <button
                  key={s}
                  onClick={() => setSortBy(s)}
                  className={`flex shrink-0 items-center gap-2 whitespace-nowrap rounded-full px-3 sm:px-4 py-2 font-semibold text-sm 
                    transition-all duration-200
                    ${
                      sortBy === s
                        ? "bg-gradient-to-r from-sky-500/[0.18] via-violet-500/[0.14] to-amber-400/[0.14] text-sky-200"
                        : "text-gray-500 hover:text-white hover:bg-white/5"
                    }`}
                >
                  {sortIcons[s]}
                  {sortLabels[s]}
                </button>
              ))}
            </div>

            {/* ASC / DESC toggle — only visible when "Created At" is selected */}
            {sortBy === "created_at" && (
              <button
                onClick={() => setDateOrder((o) => (o === "desc" ? "asc" : "desc"))}
                className="flex w-full sm:w-auto justify-center items-center gap-1.5 rounded-full border border-white/[0.06] bg-white/5 px-4 py-2 text-sm font-semibold text-sky-200 transition-all hover:bg-white/10"
              >
                {dateOrder === "desc" ? (
                  <><ArrowDownNarrowWide className="w-4 h-4" /> Newest first</>
                ) : (
                  <><ArrowUpNarrowWide className="w-4 h-4" /> Oldest first</>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      {loading && <LoadingSpinner label="Loading debates…" />}
      {error && <ErrorBox message={error} onRetry={refetch} />}
      {!loading && !error && threads?.length === 0 && (
        <EmptyState message="No debates yet. Spark one!" />
      )}

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2 xl:grid-cols-3">
        {threads.map((thread) => (
          <ThreadCard key={thread.id} thread={thread} onVote={handleVote} />
        ))}
      </div>

      {hasMore && (
        <LoadMoreButton
          onClick={loadMore}
          loading={loadingMore}
          current={threads.length}
          total={total}
        />
      )}
    </div>
  );
}
