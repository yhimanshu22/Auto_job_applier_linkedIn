import { getServerSession } from "next-auth/next";
import { NextResponse } from "next/server";

import { authOptions } from "@/lib/auth-options";

export async function GET() {
  const session: any = await getServerSession(authOptions);

  if (session?.accessToken) {
    console.log("[API] Session found, redirecting to deep link with token");
    // This performs a server-side redirect to the custom protocol
    return NextResponse.redirect(`linkdapply://auth-success?token=${session.accessToken}`);
  }

  console.log("[API] No session or token found, redirecting to login");
  return NextResponse.redirect(new URL("/login", process.env.NEXTAUTH_URL || "http://localhost:3000"));
}
