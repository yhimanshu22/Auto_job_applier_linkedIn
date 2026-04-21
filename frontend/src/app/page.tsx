import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="flex grow flex-col bg-white text-zinc-900 selection:bg-accent/10">
      {/* Header */}
      <header className="absolute top-0 z-50 flex w-full pt-6">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 md:px-8 text-zinc-900 border-b border-zinc-100 pb-4">
          <div className="flex items-center gap-8">
            <Link className="inline-flex items-center justify-center font-serif text-2xl font-bold tracking-tight hover:text-accent transition-colors" href="/">
              LinkdApply
            </Link>
            <nav className="hidden md:flex items-center gap-6">
              <Link className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors" href="/#features">
                Features
              </Link>
              <Link className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors" href="/#how-it-works">
                How it works
              </Link>
              <Link className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors" href="/#faq">
                FAQ
              </Link>
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <Link 
              className="hidden sm:inline-flex text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors" 
              href="/dashboard"
            >
              Sign in
            </Link>
            <Link 
              className="purple-gradient-button inline-flex items-center justify-center rounded-full px-6 py-2.5 text-sm font-semibold text-white transition-all hover:scale-[1.02]" 
              href="/dashboard"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      <main className="relative flex flex-col pt-32 overflow-hidden">
        {/* Background Gradients - Light Mode */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[800px] hero-gradient opacity-10 pointer-events-none"></div>

        {/* Hero Section */}
        <section className="relative flex flex-col items-center gap-12 lg:gap-20 px-6 pt-12">
          <div className="relative w-full max-w-4xl text-center space-y-8">
            <div className="space-y-4">
              <h1 className="font-serif text-[56px] lg:text-[80px] leading-[1.1] font-medium tracking-tight text-zinc-900 animate-in fade-in slide-in-from-bottom-8 duration-1000">
                #1 Undetectable <br /> 
                <span className="text-accent underline decoration-accent/20">AI Bot</span> for Job Seekers
              </h1>
              <p className="max-w-2xl mx-auto text-lg lg:text-xl text-zinc-500 leading-relaxed animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-200">
                LinkdApply takes care of the tedious job search. It manages applications, 
                tailors cover letters, and tracks updates—all while remaining completely undetectable.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-500">
              <Link 
                href="/dashboard"
                className="purple-gradient-button w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl px-10 py-4 text-white font-semibold shadow-xl transition-all hover:scale-[1.02]"
              >
                Start Applying Free
              </Link>
              <Link 
                href="#"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl border border-zinc-200 bg-white text-zinc-900 font-semibold transition-all hover:bg-zinc-50"
              >
                <svg className="size-4" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M0 3.449L9.75 2.1V11.7H0V3.449zm0 9.15h9.75V22.25L0 20.926V12.599zM11.25 1.875L24 0V11.7H11.25V1.875zm0 10.725H24v11.7L11.25 22.425V12.6z"/>
                </svg>
                Get for Windows
              </Link>
            </div>
          </div>

          {/* Hero Demo Image */}
          <div className="relative w-full max-w-6xl mx-auto px-4 perspective-midrange animate-in fade-in slide-in-from-bottom-12 duration-1000 delay-700">
            <div className="glass-card rounded-2xl overflow-hidden shadow-2xl border border-zinc-200/50 p-2 bg-white">
              <div className="bg-zinc-950 rounded-xl aspect-[1.7] flex items-center justify-center overflow-hidden border border-zinc-100">
                <div className="text-white flex flex-col items-center gap-4">
                  <div className="size-16 rounded-full bg-accent/20 flex items-center justify-center text-accent">
                    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-play fill-current"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                  </div>
                  <span className="text-zinc-500 font-medium tracking-widest text-xs uppercase">Dashboard Live Preview</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Features Split */}
        <section id="features" className="py-24 lg:py-32 bg-zinc-50 border-y border-zinc-100">
          <div className="mx-auto max-w-7xl px-6 lg:px-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-8 items-center">
              <div className="space-y-8">
                <h2 className="font-serif text-4xl lg:text-5xl font-medium tracking-tight text-zinc-900 leading-tight">
                  How LinkdApply helps <br /> you land your next role
                </h2>
                <div className="space-y-6">
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
              <div className="relative aspect-square lg:aspect-video rounded-3xl bg-zinc-950 overflow-hidden glass-card p-4 border border-zinc-100 shadow-xl">
                <div className="size-full bg-zinc-900 rounded-2xl flex items-center justify-center border border-white/5 shadow-inner">
                   <span className="text-zinc-600 text-sm italic font-mono uppercase tracking-[0.2em]">Application Engine Active</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Windows CTA Section */}
        <section className="py-24 bg-white text-zinc-900 overflow-hidden relative">
          <div className="hero-gradient absolute inset-0 opacity-10"></div>
          <div className="mx-auto max-w-7xl px-6 relative z-10">
            <div className="flex flex-col lg:flex-row items-center justify-between gap-12 lg:gap-20">
              <div className="max-w-2xl space-y-8 text-center lg:text-left">
                <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-accent/10 border border-accent/20 text-xs font-bold tracking-[0.2em] uppercase text-accent">
                   Coming to Windows
                </div>
                <h2 className="font-serif text-5xl lg:text-7xl font-medium tracking-tight leading-[1.1] text-zinc-900">
                  Job Application AI that <span className="text-accent italic tracking-tight">works for you</span>, 24/7.
                </h2>
                <p className="text-xl text-zinc-500">
                  Try LinkdApply on your Windows desktop today. Automate the boring parts of the job search while you stay focused on what matters—interviewing.
                </p>
                <div className="flex flex-col sm:flex-row items-center gap-4 pt-4 justify-center lg:justify-start">
                  <Link 
                    href="#"
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
              <div className="relative w-full max-w-xl aspect-square glass-card rounded-3xl p-8 border-white/10 flex items-center justify-center bg-white/5">
                 <div className="size-full bg-zinc-900 rounded-2xl flex items-center justify-center border border-white/5 shadow-inner">
                    <span className="text-zinc-700 text-xs font-mono uppercase tracking-[0.3em]">Desktop Environment</span>
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
                <div key={idx} className="group glass-card p-8 rounded-2xl border border-zinc-100 bg-zinc-50/50 hover:border-accent/30 transition-all hover:bg-white">
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

        {/* Footer */}
        <footer className="py-12 border-t border-zinc-100 bg-white">
          <div className="mx-auto max-w-7xl px-6 lg:px-8 flex flex-col md:row items-center justify-between gap-8">
            <span className="font-serif text-2xl font-bold tracking-tight text-zinc-900">LinkdApply</span>
            <div className="flex gap-10 text-sm font-medium text-zinc-500">
              <Link href="/terms" className="hover:text-zinc-900 transition-colors">Terms</Link>
              <Link href="/privacy" className="hover:text-zinc-900 transition-colors">Privacy</Link>
              <Link href="/support" className="hover:text-zinc-900 transition-colors">Support</Link>
            </div>
            <p className="text-xs font-bold text-zinc-400 tracking-[0.2em] uppercase">© 2024 LinkdApply. All Rights Reserved.</p>
          </div>
        </footer>
      </main>
    </div>
  );
}
