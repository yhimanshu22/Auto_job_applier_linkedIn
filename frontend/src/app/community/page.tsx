import { Metadata } from "next";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import TestimonialsGrid from "@/components/TestimonialsGrid";
import CommunityBoard from "@/components/CommunityBoard";
import { DEFAULT_TESTIMONIALS } from "@/lib/testimonials";

export const metadata: Metadata = {
  title: "Community | LinkdApply",
  description:
    "Read what job seekers say about LinkdApply and share your own feedback to help us improve.",
};

export default function CommunityPage() {
  return (
    <div className="flex grow flex-col bg-white text-zinc-900 selection:bg-accent/10">
      <Header />

      <main className="relative flex flex-col pt-32 pb-24 overflow-hidden min-h-[calc(100vh-100px)]">
        <div className="absolute top-0 left-0 w-full h-full grid-pattern pointer-events-none z-0 opacity-40" />
        <div className="absolute top-0 left-0 w-full h-full noise-texture pointer-events-none z-0" />
        <div className="absolute top-0 left-0 w-full h-[800px] natural-glow pointer-events-none z-0" />

        <div className="relative z-10 mx-auto w-full max-w-6xl px-6 space-y-20 animate-in fade-in slide-in-from-bottom-8 duration-700">
          <section className="max-w-3xl space-y-4">
            <h1 className="font-serif text-4xl lg:text-5xl font-medium tracking-tight text-zinc-900">
              Loved by job seekers across India
            </h1>
            <p className="text-lg text-zinc-500 leading-relaxed">
              Real stories from people using LinkdApply to automate LinkedIn Easy Apply — plus a
              place to share your experience and help shape what we build next.
            </p>
          </section>

          <section className="space-y-8">
            <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
              <div>
                <h2 className="font-serif text-2xl lg:text-3xl font-medium text-zinc-900">
                  What users are saying
                </h2>
                <p className="mt-2 text-zinc-500">
                  {DEFAULT_TESTIMONIALS.length} stories from the LinkdApply community
                </p>
              </div>
            </div>
            <TestimonialsGrid testimonials={DEFAULT_TESTIMONIALS} />
          </section>

          <CommunityBoard />
        </div>
      </main>

      <Footer />
    </div>
  );
}
