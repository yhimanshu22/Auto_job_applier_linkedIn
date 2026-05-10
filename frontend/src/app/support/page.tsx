import { Metadata } from 'next';
import Header from "@/components/Header";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
  title: "Support | Help & Contact",
  description: "Get in touch with the LinkdApply support team for help with your automated job search or technical inquiries.",
};

export default function SupportPage() {
  return (
    <div className="flex grow flex-col bg-white text-zinc-900 selection:bg-accent/10">
      <Header />

      <main className="relative flex flex-col pt-32 pb-24 overflow-hidden min-h-[calc(100vh-100px)]">
        {/* Background Layers */}
        <div className="absolute top-0 left-0 w-full h-full grid-pattern pointer-events-none z-0 opacity-40"></div>
        <div className="absolute top-0 left-0 w-full h-full noise-texture pointer-events-none z-0"></div>
        <div className="absolute top-0 left-0 w-full h-[800px] natural-glow pointer-events-none z-0"></div>

        <div className="relative z-10 max-w-4xl mx-auto px-6 pt-12 space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-700">
        <div className="space-y-4">
          <h1 className="font-serif text-4xl lg:text-5xl font-medium tracking-tight text-zinc-900">Get in Touch</h1>
          <p className="text-zinc-500 text-lg">We're here to help you supercharge your job search.</p>
        </div>

        <section className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-8">
          <div className="glass-card p-8 rounded-2xl border border-zinc-100 bg-zinc-50/50 hover:border-accent/20 transition-all group">
            <div className="size-12 rounded-full bg-accent/10 flex items-center justify-center text-accent mb-6 group-hover:bg-accent group-hover:text-white transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-mail"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
            </div>
            <h3 className="text-xl font-bold text-zinc-900 mb-2">Email Support</h3>
            <p className="text-zinc-500 mb-4">Expect a response within 24 hours.</p>
            <a href="mailto:himu09854@gmail.com" className="text-accent font-semibold hover:underline text-lg">himu09854@gmail.com</a>
          </div>

          <div className="glass-card p-8 rounded-2xl border border-zinc-100 bg-zinc-50/50 hover:border-accent/20 transition-all group">
            <div className="size-12 rounded-full bg-accent/10 flex items-center justify-center text-accent mb-6 group-hover:bg-accent group-hover:text-white transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-phone"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
            </div>
            <h3 className="text-xl font-bold text-zinc-900 mb-2">Call or Text</h3>
            <p className="text-zinc-500 mb-4">Available Mon-Fri, 9am - 6pm.</p>
            <a href="tel:+918114245060" className="text-accent font-semibold hover:underline text-lg">+91 8114245060</a>
          </div>
        </section>

        <section className="bg-zinc-50 rounded-3xl p-12 border border-zinc-100 space-y-4">
          <h2 className="text-2xl font-bold text-zinc-900">Priority Support</h2>
          <p className="text-zinc-600 leading-relaxed">
            For technical issues or urgent account help, please include your registered email address and detailed screenshots if possible.
          </p>
        </section>
      </div>
    </main>
      <Footer />
    </div>
  );
}
