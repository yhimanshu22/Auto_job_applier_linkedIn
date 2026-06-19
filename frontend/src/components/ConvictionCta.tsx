import Link from "next/link";

export default function ConvictionCta() {
  return (
    <section className="py-20 lg:py-28 bg-zinc-50 border-b border-zinc-100">
      <div className="mx-auto max-w-3xl px-6 text-center space-y-6">
        <h2 className="font-serif text-4xl lg:text-5xl font-medium tracking-tight text-zinc-900 leading-tight">
          Still not convinced? Start with a free account!
        </h2>
        <p className="text-lg text-zinc-500 leading-relaxed">
          LinkdApply users get on average 50% more interviews and spend 10 hours less per week.
          <br />
          Start automating your job search today.
        </p>
        <div className="flex justify-center pt-2">
          <Link
            href="/login"
            className="btn-on-light inline-flex items-center justify-center gap-2 px-10 py-4 text-base font-semibold shadow-xl transition-all hover:scale-[1.02]"
          >
            Start free trial
          </Link>
        </div>
        <p className="text-sm font-bold uppercase tracking-widest text-zinc-400">
          No credit card required
        </p>
      </div>
    </section>
  );
}
