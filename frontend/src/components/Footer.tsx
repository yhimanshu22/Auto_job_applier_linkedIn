import Link from "next/link";
import BrandLogo from "@/components/BrandLogo";

export default function Footer() {
  return (
    <footer className="py-12 border-t border-zinc-100 bg-white">
      <div className="mx-auto max-w-7xl px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-8">
        <BrandLogo height={32} withHomeLink linkClassName="text-zinc-900" />
        <div className="flex gap-10 text-sm font-medium text-zinc-500">
          <Link href="/about" className="hover:text-zinc-900 transition-colors" title="Learn more about LinkdApply">
            About
          </Link>
          <Link href="/terms" className="hover:text-zinc-900 transition-colors" title="Terms of Service">
            Terms
          </Link>
          <Link href="/privacy" className="hover:text-zinc-900 transition-colors" title="Privacy Policy">
            Privacy
          </Link>
          <Link href="/support" className="hover:text-zinc-900 transition-colors" title="Contact our support team">
            Support
          </Link>
        </div>
        <p className="text-xs font-bold text-zinc-400 tracking-[0.2em] uppercase">
          © 2026 LinkdApply v1.1.0. All Rights Reserved.
        </p>
      </div>
    </footer>
  );
}
