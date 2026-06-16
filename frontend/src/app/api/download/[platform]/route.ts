import { NextResponse } from "next/server";
import { getAssetPattern, type InstallOs } from "@/lib/install";
import { getReleaseRepo } from "@/lib/releases-server";

const VALID_PLATFORMS = new Set<InstallOs>(["windows", "mac", "linux"]);

type GitHubRelease = {
  tag_name: string;
  assets: Array<{ name: string; browser_download_url: string }>;
};

async function fetchLatestRelease(
  owner: string,
  name: string,
): Promise<GitHubRelease | null> {
  const headers: HeadersInit = {
    Accept: "application/vnd.github+json",
    "User-Agent": "linkdapply-frontend",
  };
  const token = process.env.GITHUB_TOKEN?.trim();
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(
    `https://api.github.com/repos/${owner}/${name}/releases/latest`,
    { headers, next: { revalidate: 3600 } },
  );

  if (res.status === 404) return null;
  if (!res.ok) {
    throw new Error(`GitHub API ${res.status}`);
  }

  return res.json() as Promise<GitHubRelease>;
}

export async function GET(
  _request: Request,
  context: { params: Promise<{ platform: string }> },
) {
  const { platform } = await context.params;
  if (!VALID_PLATFORMS.has(platform as InstallOs)) {
    return NextResponse.json({ error: "Unknown platform" }, { status: 400 });
  }

  const os = platform as InstallOs;
  const pattern = getAssetPattern(os);
  const repo = getReleaseRepo();

  if (!repo) {
    return NextResponse.json(
      { error: "Download is not configured yet. Please try again later." },
      { status: 503 },
    );
  }

  try {
    const release = await fetchLatestRelease(repo.owner, repo.name);
    if (!release) {
      return NextResponse.json(
        { error: "No release available yet. Please try again later." },
        { status: 404 },
      );
    }

    const asset = release.assets.find((a) => pattern.test(a.name));
    if (!asset) {
      return NextResponse.json(
        { error: `No installer found for ${os}.` },
        { status: 404 },
      );
    }

    return NextResponse.redirect(asset.browser_download_url, 302);
  } catch {
    return NextResponse.json(
      { error: "Download temporarily unavailable. Please try again later." },
      { status: 503 },
    );
  }
}
