import { Metadata } from 'next';
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import Link from "next/link";
import { COMPANY } from "@/lib/company";

export const metadata: Metadata = {
  title: "About Us | Learn More About LinkdApply AI Job Bot",
  description: "Learn about the mission behind LinkdApply — the AI-powered LinkedIn job application automation service designed to help job seekers save time and get more interviews.",
};

const SERVICES = [
  {
    name: "Free Trial",
    price: "₹0",
    period: "24 hours",
    description: "Try LinkdApply with 1 LinkedIn account, 1 active bot, and up to 10 applications. No payment required.",
  },
  {
    name: "Starter",
    price: "₹1,599",
    period: "per month",
    description: "For individual job seekers — 1 LinkedIn account, 100 applications/month, job filters, and email support.",
  },
  {
    name: "Pro",
    price: "₹3,999",
    period: "per month",
    description: "For serious job seekers — 3 LinkedIn accounts, 500 applications/month, AI dynamic answers, and priority support.",
  },
  {
    name: "Agency",
    price: "₹11,999",
    period: "per month",
    description: "For agencies and power users — 10 LinkedIn accounts, 3,000 applications/month, multi-account dashboard, and reporting.",
  },
];

export default function AboutPage() {
  return (
    <div className="flex grow flex-col bg-white text-zinc-900 selection:bg-accent/10">
      <Header />

      <main className="relative flex flex-col pt-32 pb-24 overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full grid-pattern pointer-events-none z-0 opacity-40"></div>
        <div className="absolute top-0 left-0 w-full h-full noise-texture pointer-events-none z-0"></div>
        <div className="absolute top-0 left-0 w-full h-[800px] natural-glow pointer-events-none z-0"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 w-full h-[800px] hero-gradient opacity-10 pointer-events-none z-0"></div>

        <div className="relative z-10 mx-auto max-w-4xl px-6">
          {/* Hero */}
          <section className="mb-16 text-center">
            <h1 className="font-serif text-[40px] md:text-[56px] leading-[1.1] font-medium tracking-tight text-zinc-900 mb-6">
              About <span className="text-accent">LinkdApply</span>
            </h1>
            <p className="text-xl text-zinc-600 leading-relaxed max-w-3xl mx-auto">
              {COMPANY.brandName} is an AI-powered software service that helps job seekers automate LinkedIn job
              applications — saving hours of repetitive form-filling every day.
            </p>
          </section>

          {/* Business operator — PayU requirement */}
          <section className="mb-16 p-10 rounded-3xl border border-zinc-100 bg-zinc-50/50 space-y-6">
            <h2 className="text-2xl font-bold text-zinc-900">Who We Are</h2>
            <p className="text-zinc-600 leading-relaxed">
              This website ({COMPANY.websiteUrl}) is operated by{" "}
              <span className="font-semibold text-zinc-900">{COMPANY.legalName}</span>, a sole proprietor based in
              Uttar Pradesh, India.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-sm">
              <div>
                <p className="text-xs font-bold uppercase tracking-widest text-zinc-400 mb-1">Legal Name</p>
                <p className="font-medium text-zinc-900">{COMPANY.legalName}</p>
              </div>
              <div>
                <p className="text-xs font-bold uppercase tracking-widest text-zinc-400 mb-1">Registered Address</p>
                <p className="text-zinc-700">{COMPANY.registeredAddress}</p>
              </div>
              <div>
                <p className="text-xs font-bold uppercase tracking-widest text-zinc-400 mb-1">Email</p>
                <a href={`mailto:${COMPANY.email}`} className="text-accent font-semibold hover:underline">{COMPANY.email}</a>
              </div>
              <div>
                <p className="text-xs font-bold uppercase tracking-widest text-zinc-400 mb-1">Mobile</p>
                <a href={COMPANY.phoneHref} className="text-accent font-semibold hover:underline">{COMPANY.phone}</a>
              </div>
            </div>
          </section>

          {/* What we do */}
          <section className="mb-16 space-y-6">
            <h2 className="text-2xl font-bold text-zinc-900">What We Do</h2>
            <div className="space-y-4 text-lg text-zinc-600 leading-relaxed">
              <p>
                {COMPANY.brandName} provides a subscription-based software platform (SaaS) that automates the
                LinkedIn Easy Apply process. Our service reads your resume, matches you with relevant job listings,
                fills in application forms, answers screening questions using AI, and tracks every application from
                a central dashboard.
              </p>
              <p>
                The platform is delivered entirely online — there is no physical product. Once you subscribe, access
                is activated on your account within minutes. You can install and run the automation locally on
                Windows, macOS, or Linux with a single command.
              </p>
            </div>
          </section>

          {/* Products & Services with INR prices — PayU requirement */}
          <section className="mb-16">
            <h2 className="text-2xl font-bold text-zinc-900 mb-4">Our Products &amp; Services</h2>
            <p className="text-zinc-600 mb-8">
              All prices below are in Indian Rupees (INR) and inclusive of applicable taxes. Annual plans are
              available at a discounted rate. International customers can pay in USD via Stripe — see our{" "}
              <Link href="/pricing" className="text-accent font-semibold hover:underline">Pricing page</Link>.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {SERVICES.map((service) => (
                <div
                  key={service.name}
                  className="p-6 rounded-2xl border border-zinc-100 bg-zinc-50/50 hover:border-accent/20 transition-all"
                >
                  <div className="flex items-baseline justify-between mb-3">
                    <h3 className="text-lg font-bold text-zinc-900">{service.name}</h3>
                    <div className="text-right">
                      <span className="text-2xl font-extrabold text-zinc-900">{service.price}</span>
                      <span className="text-xs text-zinc-400 ml-1">{service.period}</span>
                    </div>
                  </div>
                  <p className="text-sm text-zinc-600 leading-relaxed">{service.description}</p>
                </div>
              ))}
            </div>
            <p className="mt-6 text-center">
              <Link
                href="/pricing"
                className="btn-on-light inline-flex items-center justify-center gap-2 px-10 py-4 text-sm font-semibold shadow-xl transition-all hover:scale-[1.02]"
              >
                View Full Pricing &amp; Subscribe
              </Link>
            </p>
          </section>

          {/* Our Story */}
          <section className="mb-16 space-y-6">
            <h2 className="text-2xl font-bold text-zinc-900">Our Story</h2>
            <div className="space-y-4 text-zinc-600 leading-relaxed">
              <p>
                {COMPANY.brandName} was founded in 2026 by {COMPANY.legalName}, a software developer who spent
                hours every day manually applying to jobs on LinkedIn — copying resume details, answering the same
                screening questions, and clicking through dozens of forms.
              </p>
              <p>
                What started as a personal automation script evolved into a full platform: an AI-powered system that
                intelligently matches your profile to relevant openings and submits tailored applications on your
                behalf. Today, {COMPANY.brandName} helps job seekers across India and internationally reclaim their
                time and apply to more jobs without burnout.
              </p>
            </div>
          </section>

          {/* Values */}
          <section className="mb-16">
            <h2 className="text-2xl font-bold text-zinc-900 mb-8">What We Believe</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[
                {
                  title: "Quality Over Quantity",
                  text: "Our AI matches your resume to jobs where you are genuinely qualified. Every application is tailored, not generic.",
                },
                {
                  title: "Privacy First",
                  text: "Your data is yours. We use AES-256 encryption for stored credentials and never sell or share your personal information.",
                },
                {
                  title: "Time is Everything",
                  text: "Every hour spent filling forms is an hour you could spend learning, networking, or preparing for interviews.",
                },
                {
                  title: "Transparent & Fair",
                  text: "No contracts or hidden fees. Free trial with no credit card. Cancel anytime. Refunds within 7 days as per our policy.",
                },
              ].map((belief) => (
                <div key={belief.title} className="p-6 rounded-2xl border border-zinc-100 bg-zinc-50/50">
                  <h3 className="text-lg font-bold text-zinc-900 mb-2">{belief.title}</h3>
                  <p className="text-sm text-zinc-600 leading-relaxed">{belief.text}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Policies */}
          <section className="mb-16 p-8 rounded-3xl border border-zinc-100 bg-zinc-50/50 space-y-4">
            <h2 className="text-2xl font-bold text-zinc-900">Policies</h2>
            <p className="text-zinc-600 text-sm leading-relaxed">
              We maintain clear policies for your peace of mind:
            </p>
            <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm font-medium">
              <Link href="/privacy" className="text-accent hover:underline">Privacy Policy</Link>
              <Link href="/terms" className="text-accent hover:underline">Terms of Service</Link>
              <Link href="/refund-policy" className="text-accent hover:underline">Return &amp; Refund Policy</Link>
              <Link href="/cancellation-policy" className="text-accent hover:underline">Cancellation Policy</Link>
              <Link href="/shipping-policy" className="text-accent hover:underline">Shipping &amp; Delivery Policy</Link>
            </div>
          </section>

          {/* CTA */}
          <section className="text-center space-y-6">
            <h2 className="text-3xl font-serif font-medium text-zinc-900">Get in Touch</h2>
            <p className="text-lg text-zinc-600 max-w-2xl mx-auto">
              Questions about our service, billing, or partnerships? We are here to help.
            </p>
            <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/contact"
                className="btn-on-light inline-flex items-center justify-center gap-2 px-10 py-4 text-base font-semibold shadow-xl transition-all hover:scale-[1.02]"
              >
                Contact Us
              </Link>
              <Link
                href="/pricing"
                className="btn-secondary-light inline-flex items-center justify-center gap-2 px-10 py-4 text-base font-semibold transition-all hover:scale-[1.02]"
              >
                View Pricing
              </Link>
            </div>
          </section>
        </div>
      </main>

      <Footer />
    </div>
  );
}
