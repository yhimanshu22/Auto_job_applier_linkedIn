import type { NextAuthOptions } from "next-auth";
import GoogleProvider from "next-auth/providers/google";

/** Prefer NEXTAUTH_SECRET; dev fallback only when NODE_ENV !== production (safe for `next build`). */
function resolveAuthSecret(): string | undefined {
  const env = process.env.NEXTAUTH_SECRET?.trim();
  if (env) return env;
  if (process.env.NODE_ENV !== "production") {
    return "local-dev-only-nextauth-secret-not-for-production";
  }
  return undefined;
}

export const authOptions: NextAuthOptions = {
  secret: resolveAuthSecret(),
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID ?? "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET ?? "",
    }),
  ],
  callbacks: {
    async jwt({ token, account }) {
      if (account) {
        token.accessToken = account.access_token;
      }
      return token;
    },
    async session({ session, token }) {
      if (typeof token.accessToken === "string") {
        session.accessToken = token.accessToken;
      }
      return session;
    },
    async redirect({ baseUrl }) {
      return `${baseUrl}/api/auth/success-redirect`;
    },
  },
  pages: {
    signIn: "/login",
  },
};
