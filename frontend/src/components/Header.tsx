"use client";

import Link from "next/link";
import BrandLogo from "@/components/BrandLogo";

export default function Header() {
  return (
    <header className="absolute top-0 z-50 flex w-full pt-6">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 md:px-8 text-zinc-900 border-b border-zinc-100/50 pb-4">
        <div className="flex items-center gap-8">
          <BrandLogo height={40} priority className="opacity-95 hover:opacity-100 transition-opacity" />
          <nav className="hidden md:flex items-center gap-6">
            <Link 
              className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors" 
              href="/#features"
              title="LinkdApply Features"
            >
              Features
            </Link>
            <Link 
              className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors" 
              href="/#how-it-works"
              title="How LinkdApply Works"
            >
              How it works
            </Link>
            <Link 
              className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors" 
              href="/#faq"
              title="Frequently Asked Questions"
            >
              FAQ
            </Link>
            <Link 
              className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors" 
              href="/pricing"
              title="LinkdApply Pricing"
            >
              Pricing
            </Link>
            <Link 
              className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors" 
              href="/about"
              title="About LinkdApply"
            >
              About
            </Link>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <Link 
            className="hidden sm:inline-flex text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors" 
            href="/login"
            title="Sign in to your account"
          >
            Sign in
          </Link>
          <Link 
            className="purple-gradient-button inline-flex items-center justify-center rounded-full px-6 py-2.5 text-sm font-semibold text-white transition-all hover:scale-[1.02]" 
            href="/login"
            title="Start your free trial"
          >
            Sign up
          </Link>
        </div>
      </div>
    </header>
  );
}
