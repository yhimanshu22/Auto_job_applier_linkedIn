import Header from "@/components/Header";
import Footer from "@/components/Footer";
import Link from "next/link";
import StructuredData from "@/components/StructuredData";
import QuickInstall from "@/components/QuickInstall";
import HeroDownloadButton from "@/components/HeroDownloadButton";
import FaqAccordion from "@/components/FaqAccordion";

export default function LandingPage() {
  return (
    <div className="flex grow flex-col bg-white text-zinc-900 selection:bg-accent/10">
      <StructuredData />
      <Header />

      <main className="relative flex flex-col pt-32 overflow-hidden">
        {/* Background Gradients, Grid & Noise */}
        <div className="absolute top-0 left-0 w-full h-full grid-pattern pointer-events-none z-0 opacity-40"></div>
        <div className="absolute top-0 left-0 w-full h-full noise-texture pointer-events-none z-0"></div>
        
        {/* Top Glow */}
        <div className="absolute top-0 left-0 w-full h-[1000px] natural-glow pointer-events-none z-0"></div>
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[1000px] hero-gradient opacity-15 pointer-events-none z-0"></div>

        {/* Middle Glow */}
        <div className="absolute top-[1500px] left-0 w-full h-[1000px] natural-glow opacity-50 pointer-events-none z-0 rotate-180"></div>
        <div className="absolute top-[2000px] right-0 w-[800px] h-[800px] hero-gradient opacity-10 pointer-events-none z-0 blur-[120px]"></div>

        {/* Bottom Glow */}
        <div className="absolute bottom-0 left-0 w-full h-[1000px] natural-glow opacity-30 pointer-events-none z-0"></div>

        {/* Hero Section */}
        <section className="relative flex flex-col items-center gap-12 lg:gap-20 px-6 pt-12">
          <div className="relative w-full max-w-4xl text-center space-y-8">
            <div className="space-y-4">
              <h1 className="font-serif text-[56px] lg:text-[80px] leading-[1.1] font-medium tracking-tight text-zinc-900 animate-in fade-in slide-in-from-bottom-8 duration-1000">
                #1 Undetectable <br /> 
                <span className="text-accent underline decoration-accent/20">AI Bot</span> for Job Seekers
              </h1>
              <p className="max-w-2xl mx-auto text-lg lg:text-xl text-zinc-500 leading-relaxed animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-200">
                LinkdApply takes care of the tedious job search. Download the desktop app for Windows,
                macOS, or Linux — then automate applications while staying completely undetectable.
              </p>
            </div>

            <div className="flex justify-center animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-500">
              <HeroDownloadButton />
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
                  title: "Install & sign in",
                  description: "Download the desktop app for your OS, install it, and sign in with your account."
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

        <QuickInstall id="install" />

        {/* FAQ Section */}
        <section id="faq" className="py-24 lg:py-32 bg-white">
          <div className="mx-auto max-w-4xl px-6">
            <div className="text-center space-y-4 mb-16">
              <h2 className="font-serif text-4xl lg:text-5xl font-medium tracking-tight text-zinc-900 leading-tight">
                Frequently Asked Questions
              </h2>
              <p className="text-zinc-500">Everything you need to know about the LinkdApply automation suite.</p>
            </div>

            <FaqAccordion />
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
