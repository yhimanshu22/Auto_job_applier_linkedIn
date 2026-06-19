"use client";

import Link from "next/link";
import ProductHuntBanner from "./ProductHuntBanner";

export default function Header() {
  return (
    <header className="absolute top-0 z-50 w-full border-b border-zinc-200/80 bg-white/90 backdrop-blur-md">
      <ProductHuntBanner />
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 md:px-8 py-4 text-zinc-900">
        <div className="flex items-center gap-8">
          <Link
            href="/"
            title="LinkdApply Home"
            rel="home"
            className="flex items-center gap-2.5 font-serif text-2xl font-bold tracking-tight bg-gradient-to-r from-indigo-700 via-blue-700 to-violet-600 bg-clip-text text-transparent hover:opacity-90 transition-opacity"
          >
            <img src="/icon.png" alt="LinkdApply Logo" className="h-8 w-8 object-contain" />
            <span>LinkdApply</span>
          </Link>
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
              href="/#install"
              title="Install LinkdApply locally"
            >
              Install
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
              href="/community"
              title="Community testimonials and feedback"
            >
              Community
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
            <Link 
              className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors" 
              href="/contact"
              title="Contact Us"
            >
              Contact
            </Link>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <Link
            className="btn-on-light inline-flex items-center justify-center gap-2 px-6 py-2.5 text-sm font-semibold shadow-xl transition-all hover:scale-[1.02]"
            href="/login"
            title="Sign in to your account"
          >
            Sign in
          </Link>
        </div>
      </div>
    </header>
  );
}
