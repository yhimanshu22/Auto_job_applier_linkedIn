import { getToken } from "next-auth/jwt";
import { encode } from "next-auth/jwt";
import { NextRequest, NextResponse } from "next/server";

import { resolveAuthSecret } from "@/lib/auth-secret";

/** Issue a short-lived handoff token after browser OAuth (system browser session). */
export async function POST(req: NextRequest) {
  const secret = resolveAuthSecret();
  if (!secret) {
    return NextResponse.json({ error: "Auth not configured" }, { status: 503 });
  }

  const session = await getToken({ req, secret });
  const email = typeof session?.email === "string" ? session.email.trim() : "";
  if (!email) {
    return NextResponse.json({ error: "Not authenticated" }, { status: 401 });
  }

  const handoff = await encode({
    token: {
      sub: session?.sub ?? email,
      email,
      name: typeof session?.name === "string" ? session.name : undefined,
      purpose: "desktop-handoff",
    },
    secret,
    maxAge: 5 * 60,
  });

  return NextResponse.json({ token: handoff });
}
