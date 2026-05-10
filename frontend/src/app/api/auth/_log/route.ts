import { NextResponse } from "next/server";

/** Silence 404s when the NextAuth client posts debug payloads in development. */
export async function POST() {
  return new NextResponse(null, { status: 204 });
}
