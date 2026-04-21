import Link from "next/link";

export default function PrivacyPage() {
  return (
    <div className="flex grow flex-col bg-white text-zinc-900 selection:bg-accent/10">
      <header className="flex w-full pt-6 border-b border-zinc-100 pb-4">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 md:px-8">
          <Link className="inline-flex items-center justify-center font-serif text-2xl font-bold tracking-tight hover:text-accent transition-colors" href="/">
            LinkdApply
          </Link>
          <Link href="/" className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors">
            Back to Home
          </Link>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-16 lg:py-24 space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-700">
        <div className="space-y-4">
          <h1 className="font-serif text-4xl lg:text-5xl font-medium tracking-tight text-zinc-900">Privacy Policy</h1>
          <p className="text-zinc-500">Last updated: April 21, 2024</p>
        </div>

        <section className="space-y-6 text-zinc-700 leading-relaxed">
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">1. Data Collection</h2>
            <p>LinkdApply does not sell your personal data. We only collect the information necessary to provide and improve our service, such as your job search preferences and application history.</p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">2. LinkedIn Interaction</h2>
            <p>Our tool interacts with LinkedIn using your existing session. We do not store your LinkedIn password or credentials on our servers. All interaction data is processed locally or through secure API calls to our backend.</p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">3. Security</h2>
            <p>We implement industry-standard security measures to protect your data. Your application history and preferences are encrypted and stored securely.</p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">4. Third-Party Services</h2>
            <p>We may use third-party services (like AI providers) to process specific data related to your applications. These providers are bound by strict privacy agreements.</p>
          </div>
        </section>

        <footer className="pt-12 border-t border-zinc-100">
          <p className="text-sm text-zinc-400 italic">Questions about your privacy? Contact us on our <Link href="/support" className="text-accent hover:underline">Support</Link> page.</p>
        </footer>
      </main>
    </div>
  );
}
