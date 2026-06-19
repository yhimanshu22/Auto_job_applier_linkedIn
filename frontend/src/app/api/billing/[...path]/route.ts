import { getToken } from "next-auth/jwt";
import { NextRequest, NextResponse } from "next/server";

import { resolveAuthSecret } from "@/lib/auth-secret";

const BACKEND_URL = (process.env.BACKEND_URL || "http://127.0.0.1:8000").replace(
  /\/$/,
  ""
);

/** Stripe server callbacks — no browser session; must not require NextAuth. */
const PUBLIC_BILLING_PATHS = new Set([
  "webhook",
]);

const FORWARD_HEADERS = [
  "cookie",
  "content-type",
  "authorization",
  "accept",
  "accept-language",
  "stripe-signature",
];

async function sessionEmail(req: NextRequest): Promise<string | null> {
  const secret = resolveAuthSecret();
  if (!secret) return null;
  const token = await getToken({ req, secret });
  const email = typeof token?.email === "string" ? token.email.trim() : "";
  return email || null;
}

function attachTrustedIdentity(headers: Headers, email: string): void {
  const internalKey = process.env.LINKDAPPLY_INTERNAL_KEY?.trim();
  if (!internalKey) return;
  headers.set("X-LinkdApply-Key", internalKey);
  headers.set("X-LinkdApply-User", email);
}

async function proxyBilling(
  req: NextRequest,
  pathSegments: string[]
): Promise<NextResponse> {
  if (!process.env.BACKEND_URL && process.env.NODE_ENV === "production") {
    return NextResponse.json(
      {
        detail:
          "BACKEND_URL is not configured on Vercel. Set it to your Render API URL (e.g. https://linkedapply-backend.onrender.com).",
      },
      { status: 503 }
    );
  }

  const subpath = pathSegments.join("/");
  const isPublic = PUBLIC_BILLING_PATHS.has(subpath);
  const isMutation =
    req.method !== "GET" && req.method !== "HEAD" && req.method !== "OPTIONS";

  const target = `${BACKEND_URL}/api/billing/${subpath}${req.nextUrl.search}`;

  const headers = new Headers();
  for (const name of FORWARD_HEADERS) {
    const value = req.headers.get(name);
    if (value) headers.set(name, value);
  }

  const email = await sessionEmail(req);
  if (email) {
    attachTrustedIdentity(headers, email);
  } else if (isMutation && !isPublic) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  let body: string | undefined;
  if (isMutation) {
    body = await req.text();
  }

  try {
    const upstream = await fetch(target, {
      method: req.method,
      headers,
      body,
      cache: "no-store",
    });

    const contentType =
      upstream.headers.get("content-type") || "application/json";
    const payload = await upstream.arrayBuffer();

    return new NextResponse(payload, {
      status: upstream.status,
      headers: { "content-type": contentType },
    });
  } catch (e) {
    const message = e instanceof Error ? e.message : "Upstream request failed";
    return NextResponse.json(
      { detail: `Could not reach billing API at ${BACKEND_URL}: ${message}` },
      { status: 502 }
    );
  }
}

type RouteCtx = { params: Promise<{ path: string[] }> };

export async function GET(req: NextRequest, ctx: RouteCtx) {
  const { path } = await ctx.params;
  return proxyBilling(req, path);
}

export async function POST(req: NextRequest, ctx: RouteCtx) {
  const { path } = await ctx.params;
  return proxyBilling(req, path);
}

export async function PUT(req: NextRequest, ctx: RouteCtx) {
  const { path } = await ctx.params;
  return proxyBilling(req, path);
}

export async function DELETE(req: NextRequest, ctx: RouteCtx) {
  const { path } = await ctx.params;
  return proxyBilling(req, path);
}
