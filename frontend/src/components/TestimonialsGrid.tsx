import type { Testimonial } from "@/lib/testimonials";

type TestimonialsGridProps = {
  testimonials: Testimonial[];
};

function Stars({ rating }: { rating: number }) {
  return (
    <div className="flex gap-0.5" aria-label={`${rating} out of 5 stars`}>
      {Array.from({ length: 5 }, (_, i) => (
        <svg
          key={i}
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill={i < rating ? "currentColor" : "none"}
          stroke="currentColor"
          strokeWidth="2"
          className={i < rating ? "text-amber-400" : "text-zinc-200"}
          aria-hidden
        >
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
        </svg>
      ))}
    </div>
  );
}

export default function TestimonialsGrid({ testimonials }: TestimonialsGridProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {testimonials.map((item) => (
        <article
          key={item.id}
          className="glass-card flex flex-col rounded-2xl border border-zinc-100 bg-white p-8 shadow-sm hover:border-accent/20 hover:shadow-md transition-all"
        >
          <Stars rating={item.rating} />
          <blockquote className="mt-5 flex-1 text-zinc-600 leading-relaxed">
            &ldquo;{item.quote}&rdquo;
          </blockquote>
          <footer className="mt-6 pt-6 border-t border-zinc-100">
            <p className="font-semibold text-zinc-900">{item.name}</p>
            <p className="text-sm text-zinc-500">
              {item.role} · {item.location}
            </p>
          </footer>
        </article>
      ))}
    </div>
  );
}
