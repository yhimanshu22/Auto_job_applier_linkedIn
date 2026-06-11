import Link from "next/link";
import Header from "@/components/Header";
import Footer from "@/components/Footer";

export default function PrivacyPage() {
  return (
    <div className="flex grow flex-col bg-white text-zinc-900 selection:bg-accent/10">
      <Header />

      <main className="max-w-4xl mx-auto px-6 pt-32 pb-16 lg:py-24 lg:pt-40 space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-700">
        <div className="space-y-4">
          <h1 className="font-serif text-4xl lg:text-5xl font-medium tracking-tight text-zinc-900">
            Privacy Policy
          </h1>
          <p className="text-zinc-500">Last updated: May 10, 2026</p>
          <p className="text-sm text-zinc-600">
            This policy describes how LinkdApply (&quot;we&quot;, &quot;us&quot;) collects, uses, stores, and
            shares information when you use our website, dashboard, desktop helper, and related services
            (collectively, the &quot;Service&quot;).
          </p>
        </div>

        <section className="space-y-10 text-zinc-700 leading-relaxed">
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">1. Information we collect</h2>
            <p>We do not sell your personal information. Depending on how you use the Service, we may process:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>
                <strong className="text-zinc-900">Account and sign-in data</strong>, such as your email address
                and profile identifiers from your chosen sign-in provider (for example, Google OAuth via our
                authentication partner).
              </li>
              <li>
                <strong className="text-zinc-900">Job search and configuration data</strong>, including
                filters, preferences, and settings you save in the dashboard.
              </li>
              <li>
                <strong className="text-zinc-900">Resume and file uploads</strong>, when you upload documents
                we store or process on your behalf to complete applications.
              </li>
              <li>
                <strong className="text-zinc-900">Application activity</strong>, such as job titles, companies,
                locations, URLs, outcomes (for example applied, skipped, or failed), timestamps, and related
                notes needed to run and improve the Service.
              </li>
              <li>
                <strong className="text-zinc-900">LinkedIn session data</strong>, when you choose to sync or
                persist a session: we may store session cookies or similar tokens needed for the automation
                helper to act with your existing LinkedIn login.{' '}
                <span className="text-zinc-900 font-medium">
                  We do not ask for or store your LinkedIn password in plain text.
                </span>{' '}
                Session data is highly sensitive and should be treated like account access credentials.
              </li>
              <li>
                <strong className="text-zinc-900">Billing data</strong>, processed by our payment provider
                (for example, subscription status and customer identifiers). We do not receive your full card
                number from our processor.
              </li>
              <li>
                <strong className="text-zinc-900">API keys and secrets you provide</strong>, such as keys for
                AI providers, which we store using encryption where supported by the product.
              </li>
              <li>
                <strong className="text-zinc-900">Technical and operational data</strong>, such as IP address,
                device or app version, diagnostic logs, and error reports, to operate and secure the Service.
              </li>
            </ul>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">2. How we use information</h2>
            <p>We use the information above to:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Provide, operate, and maintain the Service (including authentication and subscriptions).</li>
              <li>Run automation features you enable, consistent with your settings and applicable terms.</li>
              <li>Generate or suggest application responses when you use integrated AI features.</li>
              <li>Improve reliability, security, and product quality; detect abuse; and comply with law.</li>
              <li>Communicate with you about the Service, billing, and important notices.</li>
            </ul>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">3. Local processing and our servers</h2>
            <p>
              Parts of the Service may run on your device (for example, a desktop helper that controls a
              browser). Some data is processed locally on your machine. Other data is sent to our backend APIs
              for sync, storage, billing, and features you use in the dashboard. The mix depends on your setup
              and which features you turn on.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">4. AI providers and prompts</h2>
            <p>
              When you enable AI-assisted features, we may send relevant content to third-party model
              providers (for example OpenAI, Google Gemini, DeepSeek, or others you configure) to generate
              suggestions or answers. That content can include job text, form questions, and material from your
              profile or resume, depending on the feature. Those providers process data under their own terms
              and privacy policies. Use AI features only with content you are allowed to share.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">5. Legal bases (EEA, UK, and similar regions)</h2>
            <p>
              Where laws such as the GDPR apply, we rely on one or more of the following: performance of a
              contract with you; legitimate interests (for example securing the Service and preventing abuse),
              balanced against your rights; consent where we expressly ask for it; and legal obligations.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">6. Sharing and subprocessors</h2>
            <p>We share information with service providers who help us run the Service, including:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Payment processing (for example Stripe).</li>
              <li>Authentication and hosting infrastructure.</li>
              <li>AI and infrastructure vendors you connect or that we integrate by default.</li>
            </ul>
            <p>
              We may also disclose information if required by law, to protect rights and safety, or as part of
              a business transfer subject to appropriate safeguards. We do not sell personal information as
              defined under applicable U.S. state privacy laws.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">7. Retention</h2>
            <p>
              We keep information only as long as needed for the purposes above, unless a longer period is
              required by law. Retention varies by data type: for example, billing records may be kept longer
              than transient logs. Application history and uploaded files may be kept until you delete them or
              close your account, subject to backup and legal holds. Session tokens should be cleared when you
              sign out or revoke access where the product supports it.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">8. Security</h2>
            <p>
              We use administrative, technical, and organizational measures designed to protect your
              information, including encryption for sensitive configuration where the product supports it.
              No method of storage or transmission is completely secure; we encourage strong passwords,
              device security, and revoking access if a device is lost.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">9. Your rights and choices</h2>
            <p>
              Depending on where you live, you may have rights to access, correct, delete, or export certain
              personal information, and to object to or restrict certain processing. You may also have the
              right to lodge a complaint with a supervisory authority. To exercise these rights, contact us
              via{' '}
              <Link href="/contact" className="text-zinc-900 underline underline-offset-2 hover:text-zinc-600">
                Contact Us
              </Link>
              . We will respond consistent with applicable law.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">10. International transfers</h2>
            <p>
              We may process and store information in countries other than where you live. Where required, we
              use appropriate safeguards (such as standard contractual clauses) for transfers from the EEA,
              UK, or Switzerland.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">11. Children</h2>
            <p>
              The Service is not directed to children. We do not knowingly collect personal information from
              anyone under 16 (or the age required in your jurisdiction). If you believe we have collected
              such information, contact us and we will take appropriate steps to delete it.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">12. Changes</h2>
            <p>
              We may update this policy from time to time. We will post the updated version on this page and
              revise the &quot;Last updated&quot; date. If changes are material, we will provide additional
              notice as required by law.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">13. Contact</h2>
            <p>
              Questions about this Privacy Policy: please reach out through{' '}
              <Link href="/contact" className="text-zinc-900 underline underline-offset-2 hover:text-zinc-600">
                Contact Us
              </Link>
              .
            </p>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
