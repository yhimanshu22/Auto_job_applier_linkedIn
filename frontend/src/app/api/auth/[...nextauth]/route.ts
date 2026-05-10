import NextAuth from "next-auth";

import { authOptions } from "@/lib/auth-options";

/** Avoid caching session/sign-in routes (Next.js App Router). */
export const dynamic = "force-dynamic";

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
