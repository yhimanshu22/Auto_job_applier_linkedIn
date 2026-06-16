export type Testimonial = {
  id: string;
  name: string;
  role: string;
  location: string;
  rating: number;
  quote: string;
};

export const DEFAULT_TESTIMONIALS: Testimonial[] = [
  {
    id: "default-1",
    name: "Priya S.",
    role: "Software Engineer",
    location: "Bangalore",
    rating: 5,
    quote:
      "I was spending 2–3 hours a day on Easy Apply. LinkdApply cut that to a 10-minute setup. I landed three interviews in the first two weeks.",
  },
  {
    id: "default-2",
    name: "Rahul M.",
    role: "Product Manager",
    location: "Mumbai",
    rating: 5,
    quote:
      "The desktop app feels native and the bot pacing is realistic. My account has stayed healthy while applications went out consistently in the background.",
  },
  {
    id: "default-3",
    name: "Ananya K.",
    role: "Data Analyst",
    location: "Hyderabad",
    rating: 5,
    quote:
      "Screening questions used to slow me down. With AI answers on Pro, I finally stopped abandoning half-filled applications mid-way.",
  },
  {
    id: "default-4",
    name: "Vikram D.",
    role: "Frontend Developer",
    location: "Pune",
    rating: 5,
    quote:
      "Filters are spot on — remote roles, experience level, and keywords. I review the application log daily and tweak settings instead of clicking the same forms again.",
  },
  {
    id: "default-5",
    name: "Sneha R.",
    role: "UX Designer",
    location: "Delhi NCR",
    rating: 4,
    quote:
      "Setup took one evening. The dashboard shows exactly what was applied and what was skipped, which builds trust when you're automating something this important.",
  },
  {
    id: "default-6",
    name: "Arjun T.",
    role: "DevOps Engineer",
    location: "Chennai",
    rating: 5,
    quote:
      "Worth it for the time saved alone. I run it on my Windows laptop while working my current job — applications keep going without me babysitting LinkedIn.",
  },
];
