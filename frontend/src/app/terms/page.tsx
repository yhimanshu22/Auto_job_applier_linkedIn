import Link from "next/link";
import Header from "@/components/Header";
import Footer from "@/components/Footer";

export default function TermsPage() {
  return (
    <div className="flex grow flex-col bg-white text-zinc-900 selection:bg-accent/10">
      <Header />

      <main className="max-w-4xl mx-auto px-6 pt-32 pb-16 lg:py-24 lg:pt-40 space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-700">
        <div className="space-y-4">
          <h1 className="font-serif text-4xl lg:text-5xl font-medium tracking-tight text-zinc-900">
            Terms of Service
          </h1>
          <p className="text-zinc-500">Last updated: May 10, 2026</p>
          <p className="text-sm text-zinc-600">
            These Terms of Service (&quot;Terms&quot;) govern your access to and use of LinkdApply&apos;s
            website, dashboard, desktop helper, and related services (collectively, the &quot;Service&quot;).
            By using the Service, you agree to these Terms. If you do not agree, do not use the Service.
          </p>
        </div>

        <section className="space-y-10 text-zinc-700 leading-relaxed">
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">1. Who we are</h2>
            <p>
              In these Terms, &quot;LinkdApply&quot;, &quot;we&quot;, &quot;us&quot;, and &quot;our&quot;
              refer to the party operating the Service. Contact details are available via{' '}
              <Link href="/support" className="text-zinc-900 underline underline-offset-2 hover:text-zinc-600">
                Support
              </Link>
              .
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">2. Eligibility</h2>
            <p>
              You must be legally able to enter a binding contract in your jurisdiction and meet any minimum
              age we specify on the Service (typically at least 16, or older where required by law). If you
              use the Service on behalf of an organization, you represent that you have authority to bind
              that organization.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">3. Description of the Service</h2>
            <p>
              LinkdApply provides tools to help you search for roles and streamline parts of the job
              application process, including optional automation and AI-assisted features. The Service may
              include a web dashboard, authentication, file storage for resumes, application history, and
              software that runs on your device to control a browser. Features, limits, and availability may
              change over time. We do not guarantee that any particular job listing will remain available,
              that an application will be submitted successfully, or that you will receive interviews or
              offers.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">4. Third-party platforms</h2>
            <p>
              The Service may interact with third-party websites and services (for example LinkedIn, job
              boards, sign-in providers, payment processors, and AI model providers). Those platforms are
              independent from LinkdApply. We are not endorsed by or affiliated with them unless we say so
              explicitly. Your use of third-party platforms is subject to their terms, policies, and technical
              requirements.{' '}
              <span className="text-zinc-900 font-medium">
                You are solely responsible for complying with the terms and rules of any platform you use with
                the Service, including rules about automation, scraping, and account activity.
              </span>{' '}
              We are not responsible for account restrictions, suspensions, loss of access, or other actions
              taken by third parties, including actions resulting from use of automation or AI tools.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">5. Your account and security</h2>
            <p>
              You must provide accurate information and keep your account credentials secure. You are
              responsible for activity under your account. Notify us promptly via Support if you suspect
              unauthorized access. You may not share accounts in a way that violates these Terms or a
              third-party platform&apos;s rules.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">6. Subscriptions, trials, and payments</h2>
            <p>
              Paid plans, free trials, and usage limits are described on the Service (for example on the
              pricing page). Payments may be processed by a third-party processor (such as Stripe). By
              subscribing, you authorize us and our payment partners to charge the payment method you provide on
              the billing cycle you select, plus applicable taxes.{' '}
              <span className="text-zinc-900 font-medium">
                Unless required by law or stated otherwise at checkout, fees are non-refundable.
              </span>{' '}
              Trials convert or end according to the terms shown when you start a trial. You may cancel
              subscriptions through the billing flows we provide; cancellation takes effect at the end of the
              current billing period unless stated otherwise. We may change prices or plans with reasonable
              notice where permitted by law.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">7. Acceptable use</h2>
            <p>You agree not to:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Use the Service for anything unlawful, fraudulent, or harmful.</li>
              <li>Harass, spam, mislead employers or platforms, or submit false qualifications.</li>
              <li>
                Attempt to interfere with, reverse engineer, or overload the Service (except to the extent
                such restriction is prohibited by applicable law).
              </li>
              <li>
                Circumvent technical limits, billing controls, or security measures, or use the Service to
                violate third-party terms.
              </li>
              <li>Access data or accounts that are not yours without authorization.</li>
            </ul>
            <p>We may suspend or terminate access for violations or risk to the Service or other users.</p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">8. AI-assisted features</h2>
            <p>
              AI-generated suggestions may be inaccurate, incomplete, or unsuitable. You are responsible for
              reviewing and editing content before submission. AI output is not legal, career, or
              professional advice. Your use of integrated AI providers may be subject to their terms and
              acceptable use policies.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">9. Intellectual property</h2>
            <p>
              The Service, including its software, branding, and documentation, is owned by LinkdApply and
              its licensors and is protected by intellectual property laws. Subject to these Terms, we grant
              you a limited, non-exclusive, non-transferable license to use the Service for your personal or
              internal business job search purposes. You retain rights to content you provide; you grant us a
              license to host, process, and display that content as needed to operate the Service.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">10. Disclaimers</h2>
            <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-5 space-y-3">
              <p>
                <strong className="text-zinc-900">No warranties.</strong> The Service is provided
                &quot;as is&quot; and &quot;as available&quot; without warranties of any kind, whether express,
                implied, or statutory, including implied warranties of merchantability, fitness for a particular
                purpose, and non-infringement, to the fullest extent permitted by law.
              </p>
              <p>
                We do not warrant uninterrupted or error-free operation, that defects will be corrected, or
                that the Service or its servers are free of harmful components.
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">11. Limitation of liability</h2>
            <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-5 space-y-3">
              <p>
                <strong className="text-zinc-900">Exclusion of damages.</strong> To the fullest extent
                permitted by law, LinkdApply and its suppliers will not be liable for any indirect,
                incidental, special, consequential, or punitive damages, or any loss of profits, data,
                goodwill, or business opportunities, arising out of or related to these Terms or the Service.
              </p>
              <p>
                <strong className="text-zinc-900">Liability cap.</strong> Our total liability for claims
                arising out of or related to the Service or these Terms will not exceed the greater of (a) the
                amounts you paid to us for the Service in the twelve (12) months before the event giving rise
                to liability, or (b) fifty U.S. dollars (USD $50), except where limitations are prohibited by
                law.
              </p>
              <p>
                Some jurisdictions do not allow certain limitations; in those cases, our liability is limited
                to the maximum extent permitted.
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">12. Indemnity</h2>
            <p>
              To the extent permitted by law, you will defend, indemnify, and hold harmless LinkdApply and its
              affiliates, officers, and agents from claims, damages, losses, and expenses (including
              reasonable attorneys&apos; fees) arising out of your use of the Service, your content, your
              violation of these Terms, or your violation of third-party rights or platform rules.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">13. Termination</h2>
            <p>
              You may stop using the Service at any time. We may suspend or terminate your access if you
              breach these Terms, create risk or legal exposure, or if we discontinue all or part of the
              Service. Provisions that by their nature should survive (including intellectual property,
              disclaimers, limitations of liability, indemnity, and governing law) will survive termination.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">14. Privacy</h2>
            <p>
              Our{' '}
              <Link href="/privacy" className="text-zinc-900 underline underline-offset-2 hover:text-zinc-600">
                Privacy Policy
              </Link>{' '}
              explains how we collect and use personal information.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">15. Changes to these Terms</h2>
            <p>
              We may modify these Terms from time to time. We will post the updated Terms on this page and
              update the &quot;Last updated&quot; date. If a change is material, we will provide additional
              notice as required by law. Continued use after the effective date constitutes acceptance of the
              updated Terms, except where your consent is required.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">16. General</h2>
            <p>
              These Terms are the entire agreement between you and LinkdApply regarding the Service and
              supersede prior agreements on the same subject. If a provision is unenforceable, the remaining
              provisions remain in effect. Our failure to enforce a provision is not a waiver. You may not
              assign these Terms without our consent; we may assign them in connection with a merger,
              acquisition, or sale of assets.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-900">17. Governing law and disputes</h2>
            <p>
              Unless mandatory consumer protection laws in your country require otherwise, these Terms are
              governed by the laws of the State of Delaware, United States, without regard to conflict of law
              principles. Courts in Delaware may have exclusive jurisdiction for disputes, subject to
              mandatory rules where you live. Before filing a claim, you agree to try to resolve the dispute
              informally by contacting us through{' '}
              <Link href="/support" className="text-zinc-900 underline underline-offset-2 hover:text-zinc-600">
                Support
              </Link>
              .
            </p>
            <p className="text-sm text-zinc-500">
              Legal terms vary by region. If you are a consumer in the EEA, UK, or other jurisdictions, you
              may have rights that cannot be waived by contract; nothing in these Terms limits those rights.
            </p>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
