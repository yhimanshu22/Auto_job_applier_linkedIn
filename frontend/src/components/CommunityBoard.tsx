"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import type { CommunityPost, CommunityReply } from "@/lib/community";

type LoadState = "loading" | "ready" | "error";

type ReplyFormProps = {
  postId: number;
  parentReplyId?: number;
  replyToName?: string;
  onSuccess: () => void;
  onCancel?: () => void;
};

function formatWhen(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function ReplyForm({ postId, parentReplyId, replyToName, onSuccess, onCancel }: ReplyFormProps) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    setSubmitting(true);
    setError("");

    const data = new FormData(form);
    const payload = {
      author_name: String(data.get("author_name") ?? "").trim(),
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
      form.reset();
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
      <input
        name="author_name"
        required
        maxLength={120}
        placeholder="Your name"
        className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
      />
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

  if (replies.length === 0) {
    return (
      <div className="mt-4 border-t border-zinc-100 pt-4">
        {activeReply === "post" ? (
          <ReplyForm
            postId={postId}
            onSuccess={() => {
              setActiveReply(null);
              onRefresh();
            }}
            onCancel={() => setActiveReply(null)}
          />
        ) : (
          <button
            type="button"
            onClick={() => setActiveReply("post")}
            className="text-sm font-semibold text-accent hover:underline"
          >
            Be the first to reply
          </button>
        )}
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
                onSuccess={() => {
                  setActiveReply(null);
                  onRefresh();
                }}
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
        <ReplyForm
          postId={postId}
          onSuccess={() => {
            setActiveReply(null);
            onRefresh();
          }}
          onCancel={() => setActiveReply(null)}
        />
      ) : null}
    </div>
  );
}

function PostCard({ post, onRefresh }: { post: CommunityPost; onRefresh: () => void }) {
  return (
    <article className="rounded-2xl border border-zinc-100 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-center gap-2 text-sm text-zinc-500">
        <span className="font-semibold text-zinc-900">{post.author_name}</span>
        <span>·</span>
        <time dateTime={post.created_at}>{formatWhen(post.created_at)}</time>
        <span>·</span>
        <span>
          {post.reply_count} {post.reply_count === 1 ? "reply" : "replies"}
        </span>
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
    const form = event.currentTarget;
    setSubmitting(true);
    setError("");

    const data = new FormData(form);
    const payload = {
      author_name: String(data.get("author_name") ?? "").trim(),
      body: String(data.get("body") ?? "").trim(),
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
      form.reset();
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-3xl border border-zinc-100 bg-zinc-50/80 p-8 lg:p-10 space-y-5"
    >
      <div className="space-y-2">
        <h2 className="font-serif text-2xl lg:text-3xl font-medium text-zinc-900">
          Share your thoughts
        </h2>
        <p className="text-zinc-500 leading-relaxed">
          Post feedback or ask the community a question.
        </p>
      </div>

      <label className="block space-y-2">
        <span className="text-sm font-medium text-zinc-700">Name</span>
        <input
          name="author_name"
          required
          maxLength={120}
          className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
          placeholder="Your name"
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
        {submitting ? "Posting…" : "Post"}
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
          Read what others are saying and join the conversation.
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
            <p className="text-center text-zinc-500 py-8">
              No posts yet — start the conversation above.
            </p>
          ) : (
            posts.map((post) => <PostCard key={post.id} post={post} onRefresh={loadPosts} />)
          )}
        </div>
      ) : null}
    </section>
  );
}
