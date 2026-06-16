import Link from 'next/link';

export default function SuccessPage() {
  return (
    <div className="min-h-screen bg-white text-zinc-900 flex flex-col justify-center items-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[800px] hero-gradient opacity-10 pointer-events-none"></div>
      
      <div className="max-w-md w-full space-y-8 bg-zinc-50/50 p-10 rounded-3xl shadow-xl border border-zinc-100 text-center relative z-10 backdrop-blur-sm">
        <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-accent/10 border border-accent/20">
          <svg className="h-8 w-8 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <div className="space-y-4">
          <h2 className="font-serif text-4xl font-medium tracking-tight text-zinc-900">Payment Successful!</h2>
          <p className="text-zinc-500 leading-relaxed">
            We've received your payment and are setting up your subscription. Your bot limits will be automatically updated.
          </p>
        </div>
        <div className="pt-6">
          <Link href="/dashboard" className="btn-on-light w-full inline-flex items-center justify-center gap-2 px-10 py-4 font-semibold shadow-xl transition-all hover:scale-[1.02]">
            Return to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
