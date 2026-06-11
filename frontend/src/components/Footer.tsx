import Link from "next/link";
import { COMPANY } from "@/lib/company";

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
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 border-t border-zinc-100 pt-8 text-center md:text-left">
          <p className="text-xs text-zinc-400 max-w-xl">
            This website is operated by {COMPANY.legalName}. Registered address: {COMPANY.registeredAddress} | {COMPANY.email} | {COMPANY.phone}
          </p>
          <p className="text-xs font-bold text-zinc-400 tracking-[0.2em] uppercase whitespace-nowrap">
            © 2026 LinkdApply v1.1.0. All Rights Reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
