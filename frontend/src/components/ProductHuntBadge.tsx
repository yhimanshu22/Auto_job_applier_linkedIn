"use client";

import { useEffect, useState } from "react";

export default function ProductHuntBadge() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Use a dynamic timestamp on the client side to avoid caching issues,
  // falling back to a default static timestamp during server-side rendering to prevent hydration mismatch.
  const timestamp = mounted ? Date.now() : "1781871279619";

  return (
    <a
      href="https://www.producthunt.com/products/linkdapply?embed=true&utm_source=badge-featured&utm_medium=badge&utm_campaign=badge-linkdapply"
      target="_blank"
      rel="noopener noreferrer"
      className="inline-block hover:scale-[1.02] active:scale-[0.98] transition-transform duration-200"
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={`https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=1175339&theme=light&t=${timestamp}`}
        alt="LinkdApply - AI applies to LinkedIn jobs while you focus on interviews | Product Hunt"
        width="250"
        height="54"
        className="w-[250px] h-[54px]"
      />
    </a>
  );
}
