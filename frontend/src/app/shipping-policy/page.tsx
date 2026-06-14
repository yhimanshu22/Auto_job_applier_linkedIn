import { Metadata } from 'next';
import Link from "next/link";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { COMPANY } from "@/lib/company";

export const metadata: Metadata = {
  title: "Shipping & Delivery Policy | LinkdApply",
  description: "LinkdApply's Shipping & Delivery Policy. LinkdApply is a digital service delivered instantly online.",
};

export default function ShippingPolicyPage() {
  return (
    <div className="flex grow flex-col bg-white text-zinc-900 selection:bg-accent/10">
      <Header />

      <main className="max-w-4xl mx-auto px-6 pt-32 pb-16 lg:py-24 lg:pt-40 space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-700">
        <div className="space-y-4">
          <h1 className="font-serif text-4xl lg:text-5xl font-medium tracking-tight text-zinc-900">
            Shipping &amp; Delivery Policy
          </h1>
          <p className="text-zinc-500">Last updated: June 11, 2026</p>
          <p className="text-sm text-zinc-600">
            This policy applies to all purchases on {COMPANY.brandName} ({COMPANY.websiteUrl}),
            operated by {COMPANY.legalName}.
          </p>
        </div>

        <section className="space-y-10 text-zinc-700 leading-relaxed">
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">1. Digital service &mdash; no physical shipping</h2>
            <p>
              {COMPANY.brandName} is a 100% digital software service (SaaS). We do not sell, ship, or deliver any
              physical products. Therefore, no shipping charges, courier services, or physical delivery timelines
              apply to any purchase made on this website.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">2. Delivery method &amp; duration</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li>
                Access to your subscription is delivered <span className="font-semibold text-zinc-900">electronically
                and instantly</span> upon successful payment confirmation &mdash; typically within{' '}
                <span className="font-semibold text-zinc-900">a few minutes, and no later than 24 hours</span>.
              </li>
              <li>
                Your plan is activated on your {COMPANY.brandName} account, and you can access all features
                immediately by signing in to your dashboard at {COMPANY.websiteUrl}.
              </li>
              <li>A payment confirmation is sent to your registered email address after every successful transaction.</li>
            </ul>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">3. Delays or activation issues</h2>
            <p>
              If your plan is not activated within 24 hours of a successful payment, please contact us at{' '}
              <a href={`mailto:${COMPANY.email}`} className="text-zinc-900 underline underline-offset-2 hover:text-zinc-600">{COMPANY.email}</a>{' '}
              or {COMPANY.phone} with your payment reference. We will resolve activation issues within{' '}
              <span className="font-semibold text-zinc-900">24&ndash;48 hours</span>, or issue a refund as per our{' '}
              <Link href="/refund-policy" className="text-zinc-900 underline underline-offset-2 hover:text-zinc-600">Return &amp; Refund Policy</Link>.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">4. Contact</h2>
            <p>
              Questions about delivery? Visit our{' '}
              <Link href="/contact" className="text-zinc-900 underline underline-offset-2 hover:text-zinc-600">Contact Us</Link>{' '}
              page or email{' '}
              <a href={`mailto:${COMPANY.email}`} className="text-zinc-900 underline underline-offset-2 hover:text-zinc-600">{COMPANY.email}</a>.
            </p>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
