const STEPS = [
  {
    step: "01",
    title: "Install & sign in",
    description:
      "Download the desktop app for your OS, install it, and sign in with your account.",
  },
  {
    step: "02",
    title: "Configure AI",
    description:
      "Tell LinkdApply about your experience and how you want to answer custom job questions.",
  },
  {
    step: "03",
    title: "Set Filters",
    description:
      "Choose your target job titles, locations, and salary expectations for the automated search.",
  },
  {
    step: "04",
    title: "Go Live",
    description:
      "Launch the bot and watch as it applies to hundreds of relevant jobs while you sleep.",
  },
];

export default function HowItWorksSteps() {
  return (
    <section id="how-it-works" className="py-24 lg:py-32 bg-white">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="text-center space-y-4 mb-16 lg:mb-24">
          <h2 className="font-serif text-4xl lg:text-6xl font-medium tracking-tight text-zinc-900 leading-tight">
            Start applying in <span className="text-accent">minutes</span>.
          </h2>
          <p className="max-w-2xl mx-auto text-lg text-zinc-500">
            Getting started with LinkdApply is simple. No complex setup, just pure automation.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {STEPS.map((item) => (
            <div
              key={item.step}
              className="relative group p-8 rounded-3xl border border-white/5 bg-zinc-50/50 hover:bg-white transition-all hover:shadow-xl"
            >
              <div className="text-4xl font-serif text-accent/20 group-hover:text-accent/40 font-bold mb-6 transition-colors">
                {item.step}
              </div>
              <h3 className="text-xl font-bold text-zinc-900 mb-3">{item.title}</h3>
              <p className="text-zinc-500 text-sm leading-relaxed">{item.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
