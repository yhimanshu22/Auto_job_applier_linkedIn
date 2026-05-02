import Header from "@/components/Header";
import Footer from "@/components/Footer";
import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="flex grow flex-col bg-white text-zinc-900 selection:bg-accent/10">
      <Header />

      <main className="relative flex flex-col pt-32 overflow-hidden">
        {/* Background Gradients, Grid & Noise */}
        <div className="absolute top-0 left-0 w-full h-[1000px] grid-pattern pointer-events-none z-0"></div>
        <div className="absolute top-0 left-0 w-full h-full noise-texture pointer-events-none z-0"></div>
        <div className="absolute top-0 left-0 w-full h-[800px] natural-glow pointer-events-none z-0"></div>
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[800px] hero-gradient opacity-10 pointer-events-none z-0"></div>

        {/* Hero Section */}
        <section className="relative flex flex-col items-center gap-12 lg:gap-20 px-6 pt-12">
          <div className="relative w-full max-w-4xl text-center space-y-8">
            <div className="space-y-4">
              <h1 className="font-serif text-[56px] lg:text-[80px] leading-[1.1] font-medium tracking-tight text-zinc-900 animate-in fade-in slide-in-from-bottom-8 duration-1000">
                #1 Undetectable <br /> 
                <span className="text-accent underline decoration-accent/20">AI Bot</span> for Job Seekers
              </h1>
              <div className="flex justify-center mt-4">
                <span className="px-3 py-1 rounded-full bg-zinc-100 border border-zinc-200 text-[10px] font-bold uppercase tracking-widest text-zinc-500">
                  Current Version: v1.1.0 (Stable)
                </span>
              </div>
              <p className="max-w-2xl mx-auto text-lg lg:text-xl text-zinc-500 leading-relaxed animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-200">
                LinkdApply takes care of the tedious job search. It manages applications, 
                tailors cover letters, and tracks updates—all while remaining completely undetectable.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-500">
              <Link 
                href="/login"
                className="purple-gradient-button w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl px-10 py-4 text-white font-semibold shadow-xl transition-all hover:scale-[1.02]"
              >
                Start Applying Free
              </Link>
              <Link 
                href="/download/LinkdApply-Setup.exe"
                download="LinkdApply-Setup.exe"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900 px-10 py-4 text-white font-semibold shadow-xl transition-all hover:bg-zinc-800 hover:scale-[1.02]"
              >
                <svg className="size-4" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M0 3.449L9.75 2.1V11.7H0V3.449zm0 9.15h9.75V22.25L0 20.926V12.599zM11.25 1.875L24 0V11.7H11.25V1.875zm0 10.725H24v11.7L11.25 22.425V12.6z"/>
                </svg>
                Get for Windows
              </Link>
            </div>
          </div>

          {/* Hero Demo Image */}
          <div className="relative w-full max-w-6xl mx-auto px-4 perspective-midrange animate-in fade-in slide-in-from-bottom-12 duration-1000 delay-700 animate-float">
            <div className="glass-card rounded-2xl overflow-hidden shadow-2xl border border-white/5 p-0 bg-zinc-950 transition-transform duration-500">
              <div className="bg-zinc-950 rounded-xl aspect-video flex items-center justify-center overflow-hidden relative shadow-inner">
                <video 
                  autoPlay 
                  loop 
                  muted 
                  playsInline
                  className="w-full h-full object-cover transition-transform duration-1000"
                >
                  <source src="/landing_page_video.mp4" type="video/mp4" />
                </video>
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-zinc-950/5">
                  <span className="text-white font-medium tracking-widest text-[9px] uppercase bg-black/40 px-3 py-1 rounded-full border border-white/10">Bot Activity Live</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Features Split */}
        <section id="features" className="py-24 lg:py-32 bg-zinc-50 border-y border-zinc-100">
          <div className="mx-auto max-w-4xl px-6 lg:px-8">
            <div className="flex flex-col items-center text-center space-y-12">
              <div className="max-w-3xl space-y-8">
                <h2 className="font-serif text-4xl lg:text-5xl font-medium tracking-tight text-zinc-900 leading-tight">
                  How LinkdApply helps <br /> you land your next role
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-12 text-left">
                  <div className="flex gap-4">
                    <div className="size-10 rounded-full bg-accent/10 flex items-center justify-center text-accent shrink-0 border border-accent/20">
                      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                    </div>
                    <div>
                      <h4 className="text-lg font-semibold text-zinc-900">Smart Context Awareness</h4>
                      <p className="text-zinc-500">The bot understands the job description in real-time and picks the best resume and cover letter for you.</p>
                    </div>
                  </div>
                  <div className="flex gap-4">
                    <div className="size-10 rounded-full bg-accent/10 flex items-center justify-center text-accent shrink-0 border border-accent/20">
                      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                    </div>
                    <div>
                      <h4 className="text-lg font-semibold text-zinc-900">Undetectable Automation</h4>
                      <p className="text-zinc-500">Mimics human behavior perfectly, ensuring your LinkedIn account stays safe while you sleep.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* How it Works Section */}
        <section id="how-it-works" className="py-24 lg:py-32 bg-white">
          <div className="mx-auto max-w-7xl px-6 lg:px-8">
            <div className="text-center space-y-4 mb-16 lg:mb-24">
               <h2 className="font-serif text-4xl lg:text-6xl font-medium tracking-tight text-zinc-900 leading-tight">
                  Start applying in <span className="text-accent italic">minutes</span>.
                </h2>
                <p className="max-w-2xl mx-auto text-lg text-zinc-500">
                  Getting started with LinkdApply is simple. No complex setup, just pure automation.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
              {[
                {
                  step: "01",
                  title: "Connect LinkedIn",
                  description: "Securely link your account using your existing session cookies. No passwords required."
                },
                {
                  step: "02",
                  title: "Configure AI",
                  description: "Tell LinkdApply about your experience and how you want to answer custom job questions."
                },
                {
                  step: "03",
                  title: "Set Filters",
                  description: "Choose your target job titles, locations, and salary expectations for the automated search."
                },
                {
                  step: "04",
                  title: "Go Live",
                  description: "Launch the bot and watch as it applies to hundreds of relevant jobs while you sleep."
                }
              ].map((item, idx) => (
                <div key={idx} className="relative group p-8 rounded-3xl border border-white/5 bg-zinc-50/50 hover:bg-white transition-all hover:shadow-xl cursor-pointer">
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

        {/* Windows CTA Section */}
        <section className="py-24 bg-white text-zinc-900 overflow-hidden relative">
          <div className="hero-gradient absolute inset-0 opacity-10"></div>
          <div className="mx-auto max-w-7xl px-6 relative z-10">
            <div className="flex flex-col items-center justify-center text-center">
              <div className="max-w-3xl space-y-8">
                <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-accent/10 border border-accent/20 text-xs font-bold tracking-[0.2em] uppercase text-accent">
                   Coming to Windows
                </div>
                <h2 className="font-serif text-5xl lg:text-7xl font-medium tracking-tight leading-[1.1] text-zinc-900">
                  Job Application AI that <span className="text-accent italic tracking-tight">works for you</span>, 24/7.
                </h2>
                <p className="text-xl text-zinc-500">
                  Try LinkdApply on your Windows desktop today. Automate the boring parts of the job search while you stay focused on what matters—interviewing.
                </p>
                <div id="download" className="flex flex-col sm:flex-row items-center gap-4 pt-4 justify-center lg:justify-start">
                  <Link 
                    href="/download/LinkdApply-Setup.exe"
                    download="LinkdApply-Setup.exe"
                    className="w-full sm:w-auto purple-gradient-button inline-flex items-center justify-center gap-2 rounded-xl px-10 py-4 text-white font-semibold shadow-2xl hover:scale-[1.02] transition-all"
                  >
                    <svg className="size-5" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M0 3.449L9.75 2.1V11.7H0V3.449zm0 9.15h9.75V22.25L0 20.926V12.599zM11.25 1.875L24 0V11.7H11.25V1.875zm0 10.725H24v11.7L11.25 22.425V12.6z"/>
                    </svg>
                    Get LinkdApply for Windows
                  </Link>
                  <span className="text-xs text-zinc-500 font-bold tracking-widest uppercase items-center flex gap-2">
                    <div className="size-1 rounded-full bg-zinc-600"></div>
                    MacOS version coming soon
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* FAQ Section */}
        <section id="faq" className="py-24 lg:py-32 bg-white">
          <div className="mx-auto max-w-4xl px-6">
            <div className="text-center space-y-4 mb-16">
              <h2 className="font-serif text-4xl lg:text-5xl font-medium tracking-tight text-zinc-900 leading-tight">
                Frequently Asked <br /> Questions
              </h2>
              <p className="text-zinc-500">Everything you need to know about the LinkdApply automation suite.</p>
            </div>

            <div className="space-y-6">
              {[
                { 
                  q: "Is LinkdApply safe to use?", 
                  a: "Yes. LinkdApply mimics human behavior with randomized delays and natural movement, making it undetectable by LinkedIn's anti-bot systems." 
                },
                { 
                  q: "How many jobs can I apply to per day?", 
                  a: "We recommend a limit of 50-100 applications per day to maintain account health, though the bot can handle more if configured." 
                },
                { 
                  q: "Does it require my LinkedIn password?", 
                  a: "No. LinkdApply uses your existing browser session and cookies to interact with LinkedIn securely, so your credentials remain private." 
                },
                { 
                  q: "Can it handle custom questions on applications?", 
                  a: "Absolutely. You can pre-configure answers to common custom questions in the 'Questions' tab of your dashboard." 
                }
              ].map((item, idx) => (
                <div key={idx} className="group glass-card p-8 rounded-2xl border border-white/5 bg-zinc-50/50 hover:border-accent/30 transition-all hover:bg-white cursor-pointer">
                  <h4 className="text-lg font-semibold text-zinc-900 mb-3 flex items-center gap-3">
                    <span className="size-6 rounded-full bg-accent/20 text-accent text-xs flex items-center justify-center shrink-0 border border-accent/20 font-bold">
                      {idx + 1}
                    </span>
                    {item.q}
                  </h4>
                  <p className="text-zinc-500 leading-relaxed pl-9 transition-colors group-hover:text-zinc-600">
                    {item.a}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Pricing CTA Section */}
        <section className="py-24 bg-zinc-50 border-t border-zinc-100">
          <div className="mx-auto max-w-4xl px-6 text-center space-y-8">
            <h2 className="font-serif text-4xl lg:text-5xl font-medium tracking-tight text-zinc-900">
              Ready to automate your job search?
            </h2>
            <p className="text-xl text-zinc-500">
              Choose a plan that fits your needs and start applying to hundreds of jobs automatically.
            </p>
            <Link 
              href="/pricing"
              className="inline-flex items-center justify-center rounded-full px-8 py-4 text-base font-semibold text-white bg-indigo-600 hover:bg-indigo-700 transition-all hover:scale-[1.02] shadow-lg"
            >
              View Pricing Plans
            </Link>
          </div>
        </section>

        <Footer />
      </main>
    </div>
  );
}
