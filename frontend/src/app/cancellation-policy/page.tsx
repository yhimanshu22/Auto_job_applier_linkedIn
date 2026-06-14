import { Metadata } from 'next';
import Link from "next/link";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { COMPANY } from "@/lib/company";

export const metadata: Metadata = {
  title: "Cancellation Policy | LinkdApply",
  description: "LinkdApply's Cancellation Policy, including how to cancel your subscription and processing duration.",
};

export default function CancellationPolicyPage() {
  return (
    <div className="flex grow flex-col bg-white text-zinc-900 selection:bg-accent/10">
      <Header />

      <main className="max-w-4xl mx-auto px-6 pt-32 pb-16 lg:py-24 lg:pt-40 space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-700">
        <div className="space-y-4">
          <h1 className="font-serif text-4xl lg:text-5xl font-medium tracking-tight text-zinc-900">
            Cancellation Policy
          </h1>
          <p className="text-zinc-500">Last updated: June 11, 2026</p>
          <p className="text-sm text-zinc-600">
            This policy applies to all subscriptions on {COMPANY.brandName} ({COMPANY.websiteUrl}),
            operated by {COMPANY.legalName}.
          </p>
        </div>

        <section className="space-y-10 text-zinc-700 leading-relaxed">
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">1. Cancel anytime</h2>
            <p>
              You may cancel your subscription at any time. There are no contracts, lock-in periods, or
              cancellation fees.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">2. How to cancel</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li>
                <span className="font-semibold text-zinc-900">From your dashboard:</span> Go to{' '}
                <span className="font-semibold text-zinc-900">Settings &rarr; Billing</span> and select
                &quot;Cancel subscription&quot;.
              </li>
              <li>
                <span className="font-semibold text-zinc-900">By email:</span> Send a cancellation request from
                your registered email address to{' '}
                <a href={`mailto:${COMPANY.email}`} className="text-zinc-900 underline underline-offset-2 hover:text-zinc-600">{COMPANY.email}</a>.
              </li>
            </ul>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">3. Cancellation duration &amp; effect</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li>
                Cancellation requests are processed within{' '}
                <span className="font-semibold text-zinc-900">24&ndash;48 hours</span> of receipt. Dashboard
                cancellations usually take effect immediately.
              </li>
              <li>
                After cancellation, your plan remains active until the{' '}
                <span className="font-semibold text-zinc-900">end of the current billing period</span> (monthly or
                yearly). You will not be charged again after that.
              </li>
              <li>No further renewals will be processed once cancellation is confirmed.</li>
              <li>
                Cancelling does not automatically trigger a refund for the current billing period. Refunds are
                governed by our{' '}
                <Link href="/refund-policy" className="text-zinc-900 underline underline-offset-2 hover:text-zinc-600">Return &amp; Refund Policy</Link>.
              </li>
            </ul>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">4. Free trial</h2>
            <p>
              The free trial expires automatically after 24 hours and requires no payment details, so no
              cancellation action is needed.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">5. Contact</h2>
            <p>
              For help with cancellation, contact {COMPANY.legalName} at{' '}
              <a href={`mailto:${COMPANY.email}`} className="text-zinc-900 underline underline-offset-2 hover:text-zinc-600">{COMPANY.email}</a>{' '}
              or {COMPANY.phone}, or visit our{' '}
              <Link href="/contact" className="text-zinc-900 underline underline-offset-2 hover:text-zinc-600">Contact Us</Link> page.
            </p>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
