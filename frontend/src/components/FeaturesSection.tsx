import Link from "next/link";

const HIGHLIGHTS = [
  "Automate LinkedIn Easy Apply while keeping human-like pacing and behavior.",
  "Review application history and track every role the bot applies to.",
  "Pre-configure answers or use AI to handle screening questions on Pro plans.",
];

export default function FeaturesSection() {
  return (
    <section id="features" className="py-24 lg:py-32 bg-zinc-50 border-y border-zinc-100">
      <div className="mx-auto max-w-6xl px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
          <div className="lg:col-span-7 space-y-6">
            <p className="text-xs font-bold uppercase tracking-widest text-accent">
              Smart job search automation
            </p>
            <h2 className="font-serif text-4xl lg:text-5xl font-medium tracking-tight text-zinc-900 leading-tight">
              Elevate your workflow with the LinkdApply desktop app
            </h2>
            <ol className="space-y-4 text-zinc-600">
              {HIGHLIGHTS.map((item, idx) => (
                <li key={item} className="flex gap-4">
                  <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-zinc-900 text-xs font-bold text-white">
                    {idx + 1}
                  </span>
                  <span className="leading-relaxed pt-0.5">{item}</span>
                </li>
              ))}
            </ol>
            <Link
              href="/login"
              className="inline-flex items-center justify-center rounded-xl border border-zinc-300 bg-white px-6 py-3 text-sm font-semibold text-zinc-800 shadow-sm transition-all hover:bg-zinc-50 hover:border-zinc-400"
            >
              Start today
            </Link>
          </div>

          <div className="lg:col-span-5">
            <div className="rounded-2xl border border-zinc-200 bg-white p-8 shadow-lg shadow-zinc-200/50">
              <div className="mb-5 flex size-12 items-center justify-center rounded-xl bg-accent/10 text-accent border border-accent/20">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-zinc-900 mb-3">
                Undetectable automation built for LinkedIn
              </h3>
              <p className="text-zinc-500 leading-relaxed">
                From smart filters to resume-aware applications and interactive question handling,
                LinkdApply streamlines your search so you can focus on interviews—not repetitive forms.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
