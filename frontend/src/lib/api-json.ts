/** Parse a fetch Response as JSON; surface HTML/404 pages as readable errors. */
export async function parseApiJson<T = Record<string, unknown>>(
  res: Response
): Promise<T> {
  const text = await res.text();
  const trimmed = text.trim();
  if (!trimmed) {
    return {} as T;
  }
  if (trimmed.startsWith("{") || trimmed.startsWith("[")) {
    try {
      return JSON.parse(trimmed) as T;
    } catch {
      throw new Error("Server returned invalid JSON.");
    }
  }
  if (trimmed.startsWith("<")) {
    const snippet = trimmed.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
    if (/not found|could not be found/i.test(snippet)) {
      throw new Error(
        "Billing API not found. Set BACKEND_URL on Vercel to your Render backend URL."
      );
    }
    throw new Error(
      snippet.slice(0, 160) || "Server returned HTML instead of JSON."
    );
  }
  throw new Error(trimmed.slice(0, 200));
}

export async function parseApiError(res: Response): Promise<string> {
  try {
    const data = await parseApiJson<{ detail?: unknown }>(res);
    const d = data?.detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) {
      return d
        .map((x: { msg?: string }) => x?.msg || "")
        .filter(Boolean)
        .join("; ");
    }
  } catch (e) {
    if (e instanceof Error) return e.message;
  }
  return res.statusText || "Request failed";
}
