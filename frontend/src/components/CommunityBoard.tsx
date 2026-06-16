"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import type { CommunityPost, CommunityReply, PostType } from "@/lib/community";

type LoadState = "loading" | "ready" | "error";

function formatWhen(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function Stars({ rating }: { rating: number }) {
  return (
    <span className="inline-flex gap-0.5 text-amber-400" aria-label={`${rating} stars`}>
      {Array.from({ length: 5 }, (_, i) => (
        <span key={i} className={i < rating ? "opacity-100" : "opacity-25"}>
          ★
        </span>
      ))}
    </span>
  );
}

function TypeBadge({ type }: { type: PostType }) {
  const label = type === "question" ? "Question" : "Feedback";
  const styles =
    type === "question"
      ? "bg-blue-50 text-blue-700 border-blue-100"
      : "bg-violet-50 text-violet-700 border-violet-100";
  return (
    <span className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${styles}`}>
      {label}
    </span>
  );
}

type ReplyFormProps = {
  postId: number;
  parentReplyId?: number;
  replyToName?: string;
  onSuccess: () => void;
  onCancel?: () => void;
};

function ReplyForm({ postId, parentReplyId, replyToName, onSuccess, onCancel }: ReplyFormProps) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    const data = new FormData(event.currentTarget);
    const payload = {
      author_name: String(data.get("author_name") ?? "").trim(),
      author_email: String(data.get("author_email") ?? "").trim(),
      body: String(data.get("body") ?? "").trim(),
      parent_reply_id: parentReplyId ?? null,
    };

    try {
      const res = await fetch(`/api/community/posts/${postId}/replies`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(
          typeof body.detail === "string" ? body.detail : "Could not post reply."
        );
      }
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-3 space-y-3 rounded-xl border border-zinc-200 bg-zinc-50 p-4">
      {replyToName ? (
        <p className="text-xs font-medium text-zinc-500">Replying to {replyToName}</p>
      ) : null}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <input
          name="author_name"
          required
          maxLength={120}
          placeholder="Your name"
          className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
        />
        <input
          name="author_email"
          type="email"
          required
          maxLength={254}
          placeholder="Email (not shown publicly)"
          className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
        />
      </div>
      <textarea
        name="body"
        required
        minLength={2}
        maxLength={2000}
        rows={3}
        placeholder="Write your reply…"
        className="w-full resize-y rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
      />
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={submitting}
          className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white hover:bg-zinc-800 disabled:opacity-60"
        >
          {submitting ? "Posting…" : "Post reply"}
        </button>
        {onCancel ? (
          <button
            type="button"
            onClick={onCancel}
            className="rounded-lg border border-zinc-200 px-4 py-2 text-sm font-medium text-zinc-600 hover:bg-white"
          >
            Cancel
          </button>
        ) : null}
      </div>
    </form>
  );
}

function ReplyThread({
  replies,
  postId,
  onRefresh,
}: {
  replies: CommunityReply[];
  postId: number;
  onRefresh: () => void;
}) {
  const [activeReply, setActiveReply] = useState<number | "post" | null>(null);

  if (replies.length === 0 && activeReply !== "post") {
    return (
      <div className="mt-4 border-t border-zinc-100 pt-4">
        <button
          type="button"
          onClick={() => setActiveReply("post")}
          className="text-sm font-semibold text-accent hover:underline"
        >
          Be the first to reply
        </button>
        {activeReply === "post" ? (
          <ReplyForm postId={postId} onSuccess={() => { setActiveReply(null); onRefresh(); }} onCancel={() => setActiveReply(null)} />
        ) : null}
      </div>
    );
  }

  return (
    <div className="mt-4 space-y-3 border-t border-zinc-100 pt-4">
      {replies.map((reply) => {
        const depth = reply.parent_reply_id ? 1 : 0;
        return (
          <div
            key={reply.id}
            className={depth > 0 ? "ml-4 sm:ml-8 border-l-2 border-zinc-100 pl-4" : ""}
          >
            <div className="rounded-xl bg-zinc-50 px-4 py-3">
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <span className="font-semibold text-zinc-900">{reply.author_name}</span>
                <span className="text-zinc-400">·</span>
                <time className="text-zinc-500" dateTime={reply.created_at}>
                  {formatWhen(reply.created_at)}
                </time>
              </div>
              <p className="mt-2 text-sm text-zinc-700 leading-relaxed whitespace-pre-wrap">
                {reply.body}
              </p>
              <button
                type="button"
                onClick={() => setActiveReply(reply.id)}
                className="mt-2 text-xs font-semibold text-accent hover:underline"
              >
                Reply
              </button>
            </div>
            {activeReply === reply.id ? (
              <ReplyForm
                postId={postId}
                parentReplyId={reply.id}
                replyToName={reply.author_name}
                onSuccess={() => { setActiveReply(null); onRefresh(); }}
                onCancel={() => setActiveReply(null)}
              />
            ) : null}
          </div>
        );
      })}

      {activeReply !== "post" ? (
        <button
          type="button"
          onClick={() => setActiveReply("post")}
          className="text-sm font-semibold text-accent hover:underline"
        >
          Add a reply
        </button>
      ) : null}
      {activeReply === "post" ? (
        <ReplyForm postId={postId} onSuccess={() => { setActiveReply(null); onRefresh(); }} onCancel={() => setActiveReply(null)} />
      ) : null}
    </div>
  );
}

function PostCard({ post, onRefresh }: { post: CommunityPost; onRefresh: () => void }) {
  return (
    <article className="rounded-2xl border border-zinc-100 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-center gap-2">
        <TypeBadge type={post.post_type} />
        {post.rating ? <Stars rating={post.rating} /> : null}
      </div>
      <h3 className="mt-3 font-serif text-xl font-medium text-zinc-900">{post.title}</h3>
      <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-zinc-500">
        <span className="font-medium text-zinc-700">{post.author_name}</span>
        <span>·</span>
        <time dateTime={post.created_at}>{formatWhen(post.created_at)}</time>
        <span>·</span>
        <span>{post.reply_count} {post.reply_count === 1 ? "reply" : "replies"}</span>
      </div>
      <p className="mt-4 text-zinc-600 leading-relaxed whitespace-pre-wrap">{post.body}</p>
      <ReplyThread replies={post.replies} postId={post.id} onRefresh={onRefresh} />
    </article>
  );
}

function NewPostForm({ onSuccess }: { onSuccess: () => void }) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    const data = new FormData(event.currentTarget);
    const ratingRaw = Number(data.get("rating") || 0);
    const payload = {
      author_name: String(data.get("author_name") ?? "").trim(),
      author_email: String(data.get("author_email") ?? "").trim(),
      title: String(data.get("title") ?? "").trim(),
      body: String(data.get("body") ?? "").trim(),
      post_type: String(data.get("post_type") ?? "feedback") as PostType,
      rating: ratingRaw >= 1 && ratingRaw <= 5 ? ratingRaw : undefined,
    };

    try {
      const res = await fetch("/api/community/posts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(
          typeof body.detail === "string" ? body.detail : "Could not create post."
        );
      }
      event.currentTarget.reset();
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-3xl border border-zinc-100 bg-zinc-50/80 p-8 lg:p-10 space-y-5">
      <div className="space-y-2">
        <h2 className="font-serif text-2xl lg:text-3xl font-medium text-zinc-900">
          Start a discussion
        </h2>
        <p className="text-zinc-500 leading-relaxed">
          Share feedback, ask a question, or help another job seeker. Your email stays private.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <label className="block space-y-2">
          <span className="text-sm font-medium text-zinc-700">Name</span>
          <input
            name="author_name"
            required
            maxLength={120}
            className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
          />
        </label>
        <label className="block space-y-2">
          <span className="text-sm font-medium text-zinc-700">Email</span>
          <input
            name="author_email"
            type="email"
            required
            maxLength={254}
            className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
            placeholder="Not shown publicly"
          />
        </label>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <label className="block space-y-2">
          <span className="text-sm font-medium text-zinc-700">Type</span>
          <select
            name="post_type"
            defaultValue="feedback"
            className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
          >
            <option value="feedback">Feedback</option>
            <option value="question">Question</option>
          </select>
        </label>
        <label className="block space-y-2">
          <span className="text-sm font-medium text-zinc-700">Rating (feedback only)</span>
          <select
            name="rating"
            defaultValue=""
            className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
          >
            <option value="">Optional</option>
            <option value="5">5 — Excellent</option>
            <option value="4">4 — Good</option>
            <option value="3">3 — Okay</option>
            <option value="2">2 — Needs work</option>
            <option value="1">1 — Poor</option>
          </select>
        </label>
      </div>

      <label className="block space-y-2">
        <span className="text-sm font-medium text-zinc-700">Title</span>
        <input
          name="title"
          required
          minLength={3}
          maxLength={200}
          className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
          placeholder="e.g. Best filters for remote roles?"
        />
      </label>

      <label className="block space-y-2">
        <span className="text-sm font-medium text-zinc-700">Message</span>
        <textarea
          name="body"
          required
          minLength={10}
          maxLength={4000}
          rows={5}
          className="w-full resize-y rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
          placeholder="Share your experience or ask the community…"
        />
      </label>

      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      <button
        type="submit"
        disabled={submitting}
        className="btn-on-light inline-flex items-center justify-center gap-2 px-8 py-3.5 text-sm font-semibold shadow-lg transition-all hover:scale-[1.02] disabled:opacity-60"
      >
        {submitting ? "Posting…" : "Post to community"}
      </button>
    </form>
  );
}

export default function CommunityBoard() {
  const [posts, setPosts] = useState<CommunityPost[]>([]);
  const [state, setState] = useState<LoadState>("loading");

  const loadPosts = useCallback(async () => {
    setState("loading");
    try {
      const res = await fetch("/api/community/posts", { cache: "no-store" });
      if (!res.ok) throw new Error("Failed to load");
      const data = await res.json();
      setPosts(data.posts ?? []);
      setState("ready");
    } catch {
      setState("error");
    }
  }, []);

  useEffect(() => {
    loadPosts();
  }, [loadPosts]);

  return (
    <section id="discussions" className="space-y-8">
      <div>
        <h2 className="font-serif text-2xl lg:text-3xl font-medium text-zinc-900">
          Community discussions
        </h2>
        <p className="mt-2 text-zinc-500">
          Ask questions, share feedback, and reply to other job seekers.
        </p>
      </div>

      <NewPostForm onSuccess={loadPosts} />

      {state === "loading" ? (
        <p className="text-center text-zinc-500 py-12">Loading discussions…</p>
      ) : null}

      {state === "error" ? (
        <div className="rounded-2xl border border-red-100 bg-red-50 px-6 py-5 text-center">
          <p className="text-red-700">Could not load discussions.</p>
          <button
            type="button"
            onClick={loadPosts}
            className="mt-3 text-sm font-semibold text-red-800 underline"
          >
            Try again
          </button>
        </div>
      ) : null}

      {state === "ready" ? (
        <div className="space-y-6">
          {posts.length === 0 ? (
            <p className="text-center text-zinc-500 py-8">No posts yet — start the conversation above.</p>
          ) : (
            posts.map((post) => (
              <PostCard key={post.id} post={post} onRefresh={loadPosts} />
            ))
          )}
        </div>
      ) : null}
    </section>
  );
}
