import Image from "next/image";
import Link from "next/link";

type BrandLogoProps = {
  /** CSS height in pixels (width follows aspect ratio). */
  height?: number;
  className?: string;
  linkClassName?: string;
  /** Wrap in home link (default true for header/footer). */
  withHomeLink?: boolean;
  priority?: boolean;
};

export default function BrandLogo({
  height = 36,
  className = "",
  linkClassName = "",
  withHomeLink = true,
  priority = false,
}: BrandLogoProps) {
  const image = (
    <Image
      src="/logo.png"
      alt="LinkdApply"
      width={280}
      height={80}
      priority={priority}
      className={`w-auto max-w-[min(280px,75vw)] object-contain object-left ${className}`}
      style={{ height, width: "auto" }}
    />
  );

  if (withHomeLink) {
    return (
      <Link
        href="/"
        title="LinkdApply Home"
        rel="home"
        className={`inline-flex items-center shrink-0 ${linkClassName}`}
      >
        {image}
      </Link>
    );
  }

  return image;
}
