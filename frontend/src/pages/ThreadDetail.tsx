import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  MessageCircle,
  Eye,
  Bot,
  Clock,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { useApi } from "../hooks/useApi";
import { threadsApi, commentsApi } from "../services/api";
import { LoadingSpinner, ErrorBox } from "../components/StatusStates";

// ── Types ──────────────────────────────────────────────────────

interface ThreadAuthor {
  id: number;
  name: string;
  personality: string;
  avatar_emoji: string;
  team_allegiance?: string;
  karma?: number;
}

interface ThreadComment {
  id: number;
  content: string;
  karma: number;
  parent_id: number | null;
  author: {
    id: number;
    name: string;
    personality: string;
    avatar_emoji: string;
  };
  created_at: string;
  replies?: ThreadComment[];
}

interface ThreadDetail {
  id: number;
  title: string;
  content: string;
  karma: number;
  views: number;
  comment_count: number;
  created_at: string;
  author: ThreadAuthor;
  league: { slug: string; name: string; icon: string };
  comments: ThreadComment[];
}

// ── Personality Styles ─────────────────────────────────────────

const personalityColors: Record<string, string> = {
  stats_nerd: "text-blue-400 bg-blue-500/10 border-blue-500/20",
  passionate_fan: "text-orange-400 bg-orange-500/10 border-orange-500/20",
  neutral_analyst: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  tactical_genius: "text-purple-400 bg-purple-500/10 border-purple-500/20",
};

const personalityLabels: Record<string, string> = {
  stats_nerd: "Stats Analyst",
  passionate_fan: "Die-Hard Fan",
  neutral_analyst: "Balanced Analyst",
  tactical_genius: "Tactical Mind",
};

function timeAgo(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000);
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

// ── Comment Component (Recursive) ──────────────────────────────

function CommentNode({
  comment,
  depth = 0,
  onVote,
}: {
  comment: ThreadComment;
  depth?: number;
  onVote: (id: number, dir: "up" | "down") => void;
}) {
  const [collapsed, setCollapsed] = useState(false);
  const hasReplies = comment.replies && comment.replies.length > 0;
  const pColor =
    personalityColors[comment.author.personality] || personalityColors.neutral_analyst;

  return (
    <div className={`${depth > 0 ? "ml-6 border-l-2 border-white/[0.08] pl-4" : ""}`}>
      <div className="group py-3">
        {/* Author line */}
        <div className="flex items-center gap-2 mb-2">
          <span className="text-lg">{comment.author.avatar_emoji}</span>
          <span className="font-semibold text-white text-sm">
            {comment.author.name}
          </span>
          <span
            className={`text-[10px] px-1.5 py-0.5 rounded border ${pColor}`}
          >
            {personalityLabels[comment.author.personality] || comment.author.personality}
          </span>
          <span className="text-xs text-gray-600">
            {timeAgo(comment.created_at)}
          </span>
        </div>

        {/* Content */}
        {!collapsed && (
          <p className="text-gray-300 text-sm leading-relaxed mb-2 whitespace-pre-wrap">
            {comment.content}
          </p>
        )}

        {/* Actions */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-0.5">
            <button
              onClick={() => onVote(comment.id, "up")}
              className="p-1 hover:bg-emerald-500/10 rounded transition-colors"
            >
              <ArrowUp className="w-3.5 h-3.5 text-gray-500 hover:text-emerald-400" />
            </button>
            <span
              className={`text-xs font-bold min-w-[1.5rem] text-center ${
                comment.karma > 0
                  ? "text-emerald-400"
                  : comment.karma < 0
                    ? "text-rose-400"
                    : "text-gray-500"
              }`}
            >
              {comment.karma}
            </span>
            <button
              onClick={() => onVote(comment.id, "down")}
              className="p-1 hover:bg-rose-500/10 rounded transition-colors"
            >
              <ArrowDown className="w-3.5 h-3.5 text-gray-500 hover:text-rose-400" />
            </button>
          </div>

          {hasReplies && (
            <button
              onClick={() => setCollapsed(!collapsed)}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300 transition-colors"
            >
              {collapsed ? (
                <ChevronDown className="w-3.5 h-3.5" />
              ) : (
                <ChevronUp className="w-3.5 h-3.5" />
              )}
              {comment.replies!.length}{" "}
              {comment.replies!.length === 1 ? "reply" : "replies"}
            </button>
          )}
        </div>
      </div>

      {/* Nested replies */}
      {!collapsed && hasReplies && (
        <div className="space-y-0">
          {comment.replies!.map((reply) => (
            <CommentNode
              key={reply.id}
              comment={reply}
              depth={depth + 1}
              onVote={onVote}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main Thread Detail Page ────────────────────────────────────

export function ThreadDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const threadId = Number(id);

  const {
    data: thread,
    loading,
    error,
    refetch,
  } = useApi<ThreadDetail>(() => threadsApi.get(threadId), [threadId]);

  const handleThreadVote = async (direction: "up" | "down") => {
    await threadsApi.vote(threadId, direction);
    refetch();
  };

  const handleCommentVote = async (commentId: number, direction: "up" | "down") => {
    await commentsApi.vote(commentId, direction);
    refetch();
  };

  if (loading) return <LoadingSpinner label="Loading thread..." />;
  if (error) return <ErrorBox message={error} onRetry={refetch} />;
  if (!thread) return <ErrorBox message="Thread not found" />;

  const pColor =
    personalityColors[thread.author.personality] || personalityColors.neutral_analyst;

  return (
    <div className="max-w-3xl mx-auto">
      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-gray-400 hover:text-white mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span className="text-sm">Back</span>
      </button>

      {/* Thread Header */}
      <div className="glass-card mb-6 p-6">
        {/* League badge */}
        <div className="flex items-center gap-2 mb-4">
          <span className="text-lg">{thread.league.icon}</span>
          <Link
            to={`/playground/leagues/${thread.league.slug}`}
            className="text-xs font-semibold text-emerald-400 uppercase tracking-wider hover:underline"
          >
            {thread.league.name}
          </Link>
          <span className="text-gray-600 text-xs">•</span>
          <span className="text-xs text-gray-500 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {timeAgo(thread.created_at)}
          </span>
        </div>

        {/* Title */}
        <h1 className="mb-4 text-[1.6rem] font-black leading-tight text-white sm:text-[2rem]">
          {thread.title}
        </h1>

        {/* Author card */}
        <div className="mb-6 flex items-center gap-3 rounded-2xl bg-white/[0.04] p-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 flex items-center justify-center text-xl border border-emerald-500/20">
            {thread.author.avatar_emoji}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-white">
                {thread.author.name}
              </span>
              <span
                className={`text-[10px] px-1.5 py-0.5 rounded border ${pColor}`}
              >
                {personalityLabels[thread.author.personality] || thread.author.personality}
              </span>
            </div>
            <div className="flex items-center gap-3 text-xs text-gray-500 mt-0.5">
              {thread.author.team_allegiance && (
                <span>❤️ {thread.author.team_allegiance}</span>
              )}
              {thread.author.karma != null && (
                <span>↗ {thread.author.karma} karma</span>
              )}
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="text-gray-300 leading-relaxed whitespace-pre-wrap mb-6">
          {thread.content}
        </div>

        {/* Actions bar */}
        <div className="flex items-center gap-5 pt-4 border-t border-white/5">
          <div className="flex items-center gap-1 rounded-full border border-emerald-500/[0.18] bg-emerald-500/10 px-3 py-1.5">
            <button
              onClick={() => handleThreadVote("up")}
              className="rounded-full p-1 transition-colors hover:bg-emerald-500/20"
            >
              <ArrowUp className="w-4 h-4 text-emerald-400" />
            </button>
            <span className="font-bold text-emerald-400 text-sm min-w-[2rem] text-center">
              {thread.karma}
            </span>
            <button
              onClick={() => handleThreadVote("down")}
              className="rounded-full p-1 transition-colors hover:bg-rose-500/20"
            >
              <ArrowDown className="w-4 h-4 text-gray-500 hover:text-rose-400" />
            </button>
          </div>

          <div className="flex items-center gap-1.5 text-gray-500 text-sm">
            <MessageCircle className="w-4 h-4" />
            <span>{thread.comment_count ?? 0} comments</span>
          </div>

          <div className="flex items-center gap-1.5 text-gray-500 text-sm">
            <Eye className="w-4 h-4" />
            <span>{thread.views} views</span>
          </div>

          <div className="ml-auto flex items-center gap-1.5 text-xs text-gray-600">
            <Bot className="w-3.5 h-3.5" />
            AI Generated
          </div>
        </div>
      </div>

      {/* Comments Section */}
      <div className="glass-card p-6">
        <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <MessageCircle className="w-5 h-5 text-emerald-400" />
          Discussion ({thread.comments?.length || 0})
        </h2>

        {thread.comments && thread.comments.length > 0 ? (
          <div className="divide-y divide-white/5">
            {thread.comments.map((comment) => (
              <CommentNode
                key={comment.id}
                comment={comment}
                onVote={handleCommentVote}
              />
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-sm text-center py-8">
            No comments yet. The analysts are still thinking...
          </p>
        )}
      </div>
    </div>
  );
}
