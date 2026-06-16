"use client";

import { useState } from "react";
import { LANDING_FAQS } from "@/lib/faq";

export default function FaqAccordion() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const toggle = (index: number) => {
    setOpenIndex((current) => (current === index ? null : index));
  };

  return (
    <div className="space-y-3">
      {LANDING_FAQS.map((item, idx) => {
        const isOpen = openIndex === idx;

        return (
          <div
            key={item.q}
            className={[
              "rounded-2xl border bg-zinc-50/50",
              isOpen
                ? "border-accent/30 bg-white shadow-sm"
                : "border-zinc-200/80 hover:border-zinc-300 hover:bg-white",
            ].join(" ")}
          >
            <button
              type="button"
              onClick={() => toggle(idx)}
              aria-expanded={isOpen}
              className="flex w-full items-center justify-between gap-4 px-6 py-5 text-left"
            >
              <span className="flex items-center gap-3 min-w-0">
                <span className="size-6 shrink-0 rounded-full bg-accent/20 text-accent text-xs flex items-center justify-center border border-accent/20 font-bold">
                  {idx + 1}
                </span>
                <span className="text-base font-semibold text-zinc-900">{item.q}</span>
              </span>
              <span
                className={[
                  "shrink-0 text-zinc-400 transition-transform duration-150",
                  isOpen ? "rotate-180" : "",
                ].join(" ")}
                aria-hidden
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              </span>
            </button>

            {isOpen && (
              <p className="px-6 pb-5 pl-13 text-zinc-500 leading-relaxed">
                {item.a}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}
