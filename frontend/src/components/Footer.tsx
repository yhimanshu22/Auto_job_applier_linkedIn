import Link from "next/link";
import { DESKTOP_VERSION } from "@/lib/install";

export default function Footer() {
  return (
    <footer className="py-12 border-t border-zinc-100 bg-white">
      <div className="mx-auto max-w-7xl px-6 lg:px-8 flex flex-col gap-10">
        <div className="flex flex-col md:flex-row items-center justify-between gap-8">
          <Link
            href="/"
            className="font-serif text-2xl font-bold tracking-tight bg-gradient-to-r from-indigo-800 via-blue-800 to-violet-700 bg-clip-text text-transparent"
          >
            LinkdApply
          </Link>
          <nav className="flex flex-wrap justify-center gap-x-8 gap-y-3 text-sm font-medium text-zinc-500">
            <Link href="/about" className="hover:text-zinc-900 transition-colors" title="Learn more about LinkdApply">
              About Us
            </Link>
            <Link href="/contact" className="hover:text-zinc-900 transition-colors" title="Contact Us">
              Contact Us
            </Link>
            <Link href="/community" className="hover:text-zinc-900 transition-colors" title="Community">
              Community
            </Link>
            <Link href="/pricing" className="hover:text-zinc-900 transition-colors" title="Plans and pricing">
              Pricing
            </Link>
            <Link href="/terms" className="hover:text-zinc-900 transition-colors" title="Terms of Service">
              Terms
            </Link>
            <Link href="/privacy" className="hover:text-zinc-900 transition-colors" title="Privacy Policy">
              Privacy Policy
            </Link>
            <Link href="/refund-policy" className="hover:text-zinc-900 transition-colors" title="Return & Refund Policy">
              Return &amp; Refund Policy
            </Link>
            <Link href="/cancellation-policy" className="hover:text-zinc-900 transition-colors" title="Cancellation Policy">
              Cancellation Policy
            </Link>
            <Link href="/shipping-policy" className="hover:text-zinc-900 transition-colors" title="Shipping & Delivery Policy">
              Shipping Policy
            </Link>
          </nav>
        </div>
        <div className="flex justify-center border-t border-zinc-100 pt-8">
          <p className="text-xs font-medium text-zinc-400 tracking-wide">
            © 2026 LinkdApply v{DESKTOP_VERSION}. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
