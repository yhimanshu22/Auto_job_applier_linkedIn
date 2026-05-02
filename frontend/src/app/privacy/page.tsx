import Header from "@/components/Header";
import Footer from "@/components/Footer";

export default function PrivacyPage() {
  return (
    <div className="flex grow flex-col bg-white text-zinc-900 selection:bg-accent/10">
      <Header />

      <main className="max-w-4xl mx-auto px-6 pt-32 pb-16 lg:py-24 lg:pt-40 space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-700">
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
      </main>
      <Footer />
    </div>
  );
}
