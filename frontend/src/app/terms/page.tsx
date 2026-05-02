import Header from "@/components/Header";
import Footer from "@/components/Footer";

export default function TermsPage() {
  return (
    <div className="flex grow flex-col bg-white text-zinc-900 selection:bg-accent/10">
      <Header />

      <main className="max-w-4xl mx-auto px-6 pt-32 pb-16 lg:py-24 lg:pt-40 space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-700">
        <div className="space-y-4">
          <h1 className="font-serif text-4xl lg:text-5xl font-medium tracking-tight text-zinc-900">Terms of Service</h1>
          <p className="text-zinc-500">Last updated: April 21, 2024</p>
        </div>

        <section className="space-y-6 text-zinc-700 leading-relaxed">
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">1. Acceptance of Terms</h2>
            <p>By accessing and using LinkdApply, you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use our services.</p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">2. Description of Service</h2>
            <p>LinkdApply is an AI-powered tool designed to assist users in automating job applications on LinkedIn. The service operates by interacting with the LinkedIn platform on behalf of the user.</p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">3. User Responsibility</h2>
            <p>Users are solely responsible for their actions while using LinkdApply. This includes compliance with LinkedIn's own Terms of Service. LinkdApply is not responsible for any account restrictions or bans resulting from the use of automation tools.</p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">4. Prohibited Use</h2>
            <p>You may not use LinkdApply for any illegal activities or to harass, spam, or otherwise violate the rights of others. Any misuse of the service may result in the termination of your access.</p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">5. Limitation of Liability</h2>
            <p>LinkdApply provides the service "as is" and makes no warranties regarding its effectiveness or reliability. We are not liable for any direct or indirect damages arising from the use of our bot.</p>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
