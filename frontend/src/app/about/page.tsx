import { Metadata } from 'next';
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import Link from "next/link";

export const metadata: Metadata = {
  title: "About Us | Our Mission to Fix Job Hunting",
  description: "Learn about the story behind LinkdApply and our mission to help job seekers automate the repetitive parts of job hunting.",
};

export default function AboutPage() {
  return (
    <div className="flex grow flex-col bg-white text-zinc-900 selection:bg-accent/10">
      <Header />

      <main className="relative flex flex-col pt-32 pb-24 overflow-hidden">
        {/* Background Layers */}
        <div className="absolute top-0 left-0 w-full h-full grid-pattern pointer-events-none z-0 opacity-40"></div>
        <div className="absolute top-0 left-0 w-full h-full noise-texture pointer-events-none z-0"></div>
        <div className="absolute top-0 left-0 w-full h-[800px] natural-glow pointer-events-none z-0"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 w-full h-[800px] hero-gradient opacity-10 pointer-events-none z-0"></div>

        <div className="relative z-10 mx-auto max-w-4xl px-6">
          {/* Mission Hero */}
          <section className="mb-20 text-center">
            <h1 className="font-serif text-[40px] md:text-[56px] leading-[1.1] font-medium tracking-tight text-zinc-900 mb-8 animate-in fade-in slide-in-from-bottom-8 duration-700">
              We're on a Mission to <br />
              <span className="text-accent italic">Fix Job Hunting</span>
            </h1>
            <p className="text-xl md:text-2xl text-zinc-600 leading-relaxed max-w-3xl mx-auto animate-in fade-in slide-in-from-bottom-8 duration-700 delay-100">
              LinkdApply was born from a simple frustration: why do job seekers spend more time filling out forms than actually preparing for interviews?
            </p>
          </section>

          {/* Our Story */}
          <section className="mb-20 space-y-6">
            <h2 className="text-2xl font-bold text-zinc-900">Our Story</h2>
            <div className="space-y-6 text-lg text-zinc-600 leading-relaxed">
              <p>
                In 2026, our founder — a software developer — found himself spending 3+ hours every single day copying and pasting the same resume details, answering the same screening questions, and clicking the same buttons across dozens of job boards. The process was soul-crushingly repetitive.
              </p>
              <p>
                So he built a tool to automate it. What started as a personal script became a full platform: an AI-powered system that reads your resume, understands your career goals, matches you with relevant openings, and submits applications on your behalf — intelligently, not blindly.
              </p>
              <p>
                Today, LinkdApply helps hundreds of job seekers reclaim their time and apply to more jobs without the burnout. We believe your time is better spent preparing for interviews, networking, and building skills — not filling repetitive forms.
              </p>
            </div>
          </section>

          {/* What We Believe */}
          <section className="mb-24">
            <h2 className="text-2xl font-bold text-zinc-900 mb-12">What We Believe</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {[
                {
                  icon: "🎯",
                  title: "Quality Over Quantity",
                  text: "We don't spray-and-pray. Our AI matches your resume to jobs where you're genuinely qualified. Every application is tailored — not generic."
                },
                {
                  icon: "🔒",
                  title: "Privacy First",
                  text: "Your data is yours. We use AES-256 encryption for all stored credentials, and we never sell or share your personal information with anyone."
                },
                {
                  icon: "⚡",
                  title: "Time is Everything",
                  text: "Every hour spent filling forms is an hour you could spend learning, networking, or interview prepping. We give that time back to you."
                },
                {
                  icon: "🤝",
                  title: "Transparent & Fair",
                  text: "No contracts, no lock-ins, no hidden fees. Our free trial requires zero credit card. Cancel anytime. We earn your trust, not trap you."
                }
              ].map((belief, idx) => (
                <div key={idx} className="p-8 rounded-3xl border border-zinc-100 bg-zinc-50/50 hover:border-accent/20 transition-all hover:bg-white hover:shadow-xl group">
                  <div className="text-3xl mb-4 group-hover:scale-110 transition-transform inline-block">{belief.icon}</div>
                  <h3 className="text-xl font-bold text-zinc-900 mb-3">{belief.title}</h3>
                  <p className="text-zinc-600 leading-relaxed text-sm">{belief.text}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Technology */}
          <section className="mb-24 p-10 rounded-[32px] bg-zinc-950 text-white relative overflow-hidden group">
             <div className="absolute top-0 left-0 w-full h-full hero-gradient opacity-30 pointer-events-none"></div>
             <div className="relative z-10 space-y-8">
                <div className="space-y-4">
                  <h2 className="text-2xl font-bold">Our Technology</h2>
                  <p className="text-zinc-400 leading-relaxed">
                    LinkdApply is built on a high-performance, modern stack designed for reliability, speed, and undetectability. 
                  </p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div className="space-y-2">
                    <h4 className="text-accent font-bold uppercase tracking-widest text-xs">Core Frameworks</h4>
                    <p className="text-sm text-zinc-400">Next.js 15 for a lightning-fast frontend, FastAPI for a robust Python backend, and Electron for a seamless desktop experience.</p>
                  </div>
                  <div className="space-y-2">
                    <h4 className="text-accent font-bold uppercase tracking-widest text-xs">AI Engine</h4>
                    <p className="text-sm text-zinc-400">Integrated with OpenAI, Google Gemini, and DeepSeek to intelligently parse job descriptions and generate human-like responses.</p>
                  </div>
                  <div className="space-y-2">
                    <h4 className="text-accent font-bold uppercase tracking-widest text-xs">Automation</h4>
                    <p className="text-sm text-zinc-400">Powered by Selenium and Playwright with custom behavioral scripts to mimic human interaction and bypass anti-bot detections.</p>
                  </div>
                  <div className="space-y-2">
                    <h4 className="text-accent font-bold uppercase tracking-widest text-xs">Security & Billing</h4>
                    <p className="text-sm text-zinc-400">Secure AES-256 data encryption with global payment support via Stripe for a seamless checkout experience.</p>
                  </div>
                </div>
             </div>
          </section>

          {/* Get in Touch */}
          <section className="text-center space-y-6">
            <h2 className="text-3xl font-serif font-medium text-zinc-900">Get in Touch</h2>
            <p className="text-lg text-zinc-600 max-w-2xl mx-auto">
              Have questions, feedback, or partnership inquiries? We'd love to hear from you.
            </p>
            <div className="pt-4">
              <Link 
                href="/support"
                className="inline-flex items-center justify-center rounded-full px-10 py-4 text-base font-semibold text-white purple-gradient-button hover:scale-[1.02] transition-all shadow-xl"
              >
                Contact Support
              </Link>
            </div>
          </section>
        </div>
      </main>

      <Footer />
    </div>
  );
}
