import { Metadata } from 'next';
import Link from "next/link";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { COMPANY } from "@/lib/company";

export const metadata: Metadata = {
  title: "Return & Refund Policy | LinkdApply",
  description: "LinkdApply's Return & Refund Policy, including eligibility, refund duration, and refund mode.",
};

export default function RefundPolicyPage() {
  return (
    <div className="flex grow flex-col bg-white text-zinc-900 selection:bg-accent/10">
      <Header />

      <main className="max-w-4xl mx-auto px-6 pt-32 pb-16 lg:py-24 lg:pt-40 space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-700">
        <div className="space-y-4">
          <h1 className="font-serif text-4xl lg:text-5xl font-medium tracking-tight text-zinc-900">
            Return &amp; Refund Policy
          </h1>
          <p className="text-zinc-500">Last updated: June 11, 2026</p>
          <p className="text-sm text-zinc-600">
            This policy applies to all paid subscriptions purchased on {COMPANY.brandName} ({COMPANY.websiteUrl}),
            operated by {COMPANY.legalName}.
          </p>
        </div>

        <section className="space-y-10 text-zinc-700 leading-relaxed">
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">1. Nature of our service</h2>
            <p>
              {COMPANY.brandName} is a digital software service (SaaS). We do not sell or ship physical goods,
              so traditional product &quot;returns&quot; do not apply. Instead, this policy describes when and
              how you can request a refund for a paid subscription.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">2. Refund eligibility &amp; duration</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li>
                <span className="font-semibold text-zinc-900">7-day refund window:</span> You may request a full
                refund within <span className="font-semibold text-zinc-900">7 days</span> of your first purchase of
                a paid plan if you are not satisfied with the Service.
              </li>
              <li>
                Refund requests made after 7 days from the date of purchase are not eligible, except where a
                verified technical failure on our side prevented you from using the Service.
              </li>
              <li>
                Renewal charges are eligible for a refund if the request is made within
                <span className="font-semibold text-zinc-900"> 48 hours</span> of the renewal and the Service has
                not been substantially used in the new billing period.
              </li>
              <li>The free trial requires no payment and is therefore not eligible for any refund.</li>
              <li>
                Refunds may be refused in cases of misuse, violation of our{' '}
                <Link href="/terms" className="text-zinc-900 underline underline-offset-2 hover:text-zinc-600">Terms of Service</Link>,
                or fraudulent activity.
              </li>
            </ul>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">3. How to request a refund</h2>
            <p>
              Email us at{' '}
              <a href={`mailto:${COMPANY.email}`} className="text-zinc-900 underline underline-offset-2 hover:text-zinc-600">{COMPANY.email}</a>{' '}
              from your registered email address with the subject &quot;Refund Request&quot;, including your plan
              name, date of purchase, and the reason for the request. You can also reach us via the{' '}
              <Link href="/contact" className="text-zinc-900 underline underline-offset-2 hover:text-zinc-600">Contact Us</Link> page.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">4. Refund mode &amp; processing time</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li>
                Approved refunds are issued to the <span className="font-semibold text-zinc-900">original payment
                method</span> used for the purchase (e.g. credit/debit card, UPI, net banking, or wallet).
              </li>
              <li>
                Refunds are processed within <span className="font-semibold text-zinc-900">5&ndash;7 business days</span>{' '}
                of approval. Depending on your bank or card issuer, it may take an additional 5&ndash;10 business
                days for the amount to reflect in your account.
              </li>
              <li>Refunds are issued in the same currency in which the payment was made (INR for Indian customers; USD for international payments processed via Stripe).</li>
            </ul>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">5. Contact</h2>
            <p>
              Questions about this policy? Contact {COMPANY.legalName} at{' '}
              <a href={`mailto:${COMPANY.email}`} className="text-zinc-900 underline underline-offset-2 hover:text-zinc-600">{COMPANY.email}</a>{' '}
              or {COMPANY.phone}.
            </p>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
