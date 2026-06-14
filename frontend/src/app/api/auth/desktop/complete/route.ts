import { decode, encode } from "next-auth/jwt";
import { NextRequest, NextResponse } from "next/server";

import { resolveAuthSecret } from "@/lib/auth-secret";

/** Exchange a desktop handoff token for a NextAuth session cookie in the app WebView. */
export async function GET(req: NextRequest) {
  const secret = resolveAuthSecret();
  const loginUrl = new URL("/login?desktop=1", req.url);

  if (!secret) {
    return NextResponse.redirect(loginUrl);
  }

  const handoff = req.nextUrl.searchParams.get("token")?.trim();
  if (!handoff) {
    return NextResponse.redirect(loginUrl);
  }

  let payload: Record<string, unknown> | null = null;
  try {
    payload = (await decode({ token: handoff, secret })) as Record<
      string,
      unknown
    > | null;
  } catch {
    payload = null;
  }

  const email =
    typeof payload?.email === "string" ? payload.email.trim() : "";
  if (!email || payload?.purpose !== "desktop-handoff") {
    return NextResponse.redirect(
      new URL("/login?desktop=1&error=desktop_auth", req.url)
    );
  }

  const sessionToken = await encode({
    token: {
      sub: typeof payload.sub === "string" ? payload.sub : email,
      email,
      name: typeof payload.name === "string" ? payload.name : undefined,
    },
    secret,
    maxAge: 30 * 24 * 60 * 60,
  });

  const isSecure = req.nextUrl.protocol === "https:";
  const cookieName = isSecure
    ? "__Secure-next-auth.session-token"
    : "next-auth.session-token";

  const response = NextResponse.redirect(
    new URL("/dashboard?desktop=1", req.url)
  );
  response.cookies.set(cookieName, sessionToken, {
    httpOnly: true,
    secure: isSecure,
    sameSite: "lax",
    path: "/",
    maxAge: 30 * 24 * 60 * 60,
  });

  return response;
}
