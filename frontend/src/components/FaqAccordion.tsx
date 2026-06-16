import Link from "next/link";
import { LANDING_FAQS } from "@/lib/faq";

export default function FaqAccordion() {
  return (
    <div className="flex flex-col gap-4 text-left">
      {LANDING_FAQS.map((item) => (
        <details
          key={item.q}
          className="group rounded-xl border border-zinc-200 bg-white px-5 py-4 shadow-sm open:border-accent/30 open:shadow-md transition-shadow"
        >
          <summary className="cursor-pointer list-none text-base font-semibold text-zinc-900 flex items-center justify-between gap-4 [&::-webkit-details-marker]:hidden">
            {item.q}
            <span className="shrink-0 text-zinc-400 group-open:rotate-180 transition-transform duration-150" aria-hidden>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </span>
          </summary>
          <p className="mt-3 text-zinc-500 leading-relaxed">{item.a}</p>
        </details>
      ))}
    </div>
  );
}

export function FaqSectionHeader() {
  return (
    <div className="text-center space-y-4 mb-12">
      <h2 className="font-serif text-4xl lg:text-5xl font-medium tracking-tight text-zinc-900 leading-tight">
        Frequently Asked Questions
      </h2>
      <p className="text-zinc-500">
        Everything you need to know about LinkdApply. See our{" "}
        <Link href="/pricing" className="text-accent underline underline-offset-2 hover:text-accent/80">
          pricing page
        </Link>
        .
      </p>
    </div>
  );
}
