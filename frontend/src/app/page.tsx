import Header from "@/components/Header";
import Footer from "@/components/Footer";
import Link from "next/link";
import StructuredData from "@/components/StructuredData";
import QuickInstall from "@/components/QuickInstall";
import HeroDownloadButton from "@/components/HeroDownloadButton";
import FaqAccordion, { FaqSectionHeader } from "@/components/FaqAccordion";
import FeaturesSection from "@/components/FeaturesSection";
import HowItWorksSteps from "@/components/HowItWorksSteps";
import ConvictionCta from "@/components/ConvictionCta";
import TestimonialsGrid from "@/components/TestimonialsGrid";
import { DEFAULT_TESTIMONIALS } from "@/lib/testimonials";
import ProductHuntBadge from "@/components/ProductHuntBadge";

export default function LandingPage() {
  return (
    <div className="flex grow flex-col bg-white text-zinc-900 selection:bg-accent/10">
      <StructuredData />
      <Header />

      <main className="relative flex flex-col pt-32 overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full grid-pattern pointer-events-none z-0 opacity-40" />
        <div className="absolute top-0 left-0 w-full h-full noise-texture pointer-events-none z-0" />
        <div className="absolute top-0 left-0 w-full h-[1000px] natural-glow pointer-events-none z-0" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[1000px] hero-gradient opacity-15 pointer-events-none z-0" />
        <div className="absolute top-[1500px] left-0 w-full h-[1000px] natural-glow opacity-50 pointer-events-none z-0 rotate-180" />
        <div className="absolute top-[2000px] right-0 w-[800px] h-[800px] hero-gradient opacity-10 pointer-events-none z-0 blur-[120px]" />
        <div className="absolute bottom-0 left-0 w-full h-[1000px] natural-glow opacity-30 pointer-events-none z-0" />

        {/* Hero */}
        <section className="relative flex flex-col items-center gap-12 lg:gap-16 px-6 pt-12 pb-8">
          <div className="relative w-full max-w-4xl text-center space-y-8">
            <div className="flex justify-center animate-in fade-in slide-in-from-bottom-8 duration-1000">
              <ProductHuntBadge />
            </div>

            <div className="space-y-4">
              <h1 className="font-serif text-[56px] lg:text-[80px] leading-[1.1] font-medium tracking-tight text-zinc-900 animate-in fade-in slide-in-from-bottom-8 duration-1000">
                #1 Undetectable <br />
                <span className="text-accent underline decoration-accent/20">AI Bot</span> for Job Seekers
              </h1>
              <p className="max-w-2xl mx-auto text-lg lg:text-xl text-zinc-500 leading-relaxed animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-200">
                Download the LinkdApply desktop app, set your filters, and let AI submit Easy Apply
                applications on your behalf — full control, zero repetitive form filling.
              </p>
            </div>

            <div className="flex justify-center animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-500">
              <HeroDownloadButton />
            </div>
          </div>

          <div className="relative w-full max-w-6xl mx-auto px-4 perspective-midrange animate-in fade-in slide-in-from-bottom-12 duration-1000 delay-700 animate-float">
            <div className="glass-card rounded-2xl overflow-hidden shadow-2xl border border-white/5 p-0 bg-zinc-950 transition-transform duration-500">
              <div className="bg-zinc-950 rounded-xl aspect-video flex items-center justify-center overflow-hidden relative shadow-inner">
                <img
                  src="/landing_page_video.gif"
                  alt="LinkdApply Automation Demo"
                  className="w-full h-full object-cover transition-transform duration-1000"
                  loading="lazy"
                />
              </div>
            </div>
          </div>
        </section>

        <FeaturesSection />
        <HowItWorksSteps />
        <QuickInstall id="install" />

        {/* Testimonials */}
        <section className="py-24 lg:py-32 bg-zinc-50 border-b border-zinc-100">
          <div className="mx-auto max-w-6xl px-6 space-y-12">
            <div className="text-center max-w-3xl mx-auto space-y-4">
              <h2 className="font-serif text-4xl lg:text-5xl font-medium tracking-tight text-zinc-900">
                Loved by job seekers across the world
              </h2>
              <p className="text-lg text-zinc-500 leading-relaxed">
                See how other job seekers are saving hundreds of hours and getting more interviews with LinkdApply.
              </p>
            </div>
            <TestimonialsGrid testimonials={DEFAULT_TESTIMONIALS} />
          </div>
        </section>

        <section id="faq" className="py-24 lg:py-32 bg-white border-b border-zinc-100">
          <div className="mx-auto max-w-3xl px-6">
            <FaqSectionHeader />
            <FaqAccordion />
          </div>
        </section>

        <ConvictionCta />

        <section className="py-20 bg-white border-t border-zinc-100">
          <div className="mx-auto max-w-4xl px-6 text-center space-y-6">
            <h2 className="font-serif text-3xl lg:text-4xl font-medium tracking-tight text-zinc-900">
              Ready to automate your job search?
            </h2>
            <p className="text-lg text-zinc-500">
              Compare plans and pick the right application limits for your search.
            </p>
            <Link
              href="/pricing"
              className="btn-on-light inline-flex items-center justify-center gap-2 px-10 py-4 text-base font-semibold shadow-xl transition-all hover:scale-[1.02]"
            >
              View pricing plans
            </Link>
          </div>
        </section>

        <Footer />
      </main>
    </div>
  );
}
