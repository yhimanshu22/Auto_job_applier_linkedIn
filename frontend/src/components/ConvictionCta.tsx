import Link from "next/link";

export default function ConvictionCta() {
  return (
    <section className="py-20 lg:py-28 bg-zinc-950">
      <div className="mx-auto max-w-3xl px-6 text-center space-y-6">
        <h2 className="font-serif text-4xl lg:text-5xl font-medium tracking-tight text-white leading-tight">
          Still not convinced? Start with a free account!
        </h2>
        <p className="text-lg text-zinc-300 leading-relaxed">
          LinkdApply users get on average 50% more interviews and spend 10 hours less per week.
          <br />
          Start automating your job search today.
        </p>
        <div className="flex justify-center pt-2">
          <Link
            href="/login"
            className="inline-flex items-center justify-center rounded-xl bg-white px-10 py-4 text-base font-semibold text-zinc-900 shadow-xl transition-all hover:scale-[1.02] hover:bg-zinc-100"
          >
            Start free trial
          </Link>
        </div>
        <p className="text-sm font-bold uppercase tracking-widest text-zinc-500">
          No credit card required
        </p>
      </div>
    </section>
  );
}
