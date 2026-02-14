import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "How pruv collects, uses, and protects your data.",
};

export default function PrivacyPage() {
  return (
    <div className="page">
      <div className="container">
        <div className="page-header">
          <div className="section-label">privacy</div>
          <h1>Privacy Policy</h1>
          <p>Last updated: January 15, 2025</p>
        </div>

        <div className="page-body">
          <h2>1. Introduction</h2>
          <p>
            pruv (&ldquo;we,&rdquo; &ldquo;our,&rdquo; or &ldquo;us&rdquo;) is
            committed to protecting your privacy. This Privacy Policy explains
            how we collect, use, disclose, and safeguard your information when
            you use the pruv platform, API, SDK, and website (collectively, the
            &ldquo;Service&rdquo;).
          </p>

          <h2>2. Information we collect</h2>

          <h3>Account information</h3>
          <p>
            When you create an account, we collect your email address, name, and
            authentication credentials. If you sign up via OAuth (GitHub,
            Google), we receive your profile information from the provider.
          </p>

          <h3>Verification data</h3>
          <p>
            When you use the pruv SDK or API, we receive XY records containing
            hashed state data. By default, pruv transmits only cryptographic
            hashes of your data, not the raw data itself. If you choose to store
            full state snapshots, that data is encrypted at rest with
            AES-256-GCM.
          </p>

          <h3>Auto-redaction</h3>
          <p>
            pruv automatically redacts detected secrets (API keys, passwords,
            tokens) before storing chain data. This feature is enabled by default
            and can be controlled via the PRUV_AUTO_REDACT environment variable.
          </p>

          <h3>Usage data</h3>
          <p>
            We collect information about how you interact with the Service,
            including API call frequency, feature usage, and error rates. This
            data is used to improve the Service and is not sold to third parties.
          </p>

          <h2>3. How we use your information</h2>
          <ul>
            <li>Provide, maintain, and improve the Service</li>
            <li>Store and verify your XY chains and generate receipts</li>
            <li>Process transactions and send related information</li>
            <li>Send technical notices, updates, and security alerts</li>
            <li>Respond to your comments, questions, and support requests</li>
            <li>Monitor and analyze trends, usage, and activities</li>
            <li>
              Detect, investigate, and prevent fraudulent or unauthorized
              activity
            </li>
          </ul>

          <h2>4. Data retention</h2>
          <p>
            Verification records are retained according to your plan: Free (7
            days), Pro (90 days), Team (1 year), Enterprise (custom). Account
            information is retained as long as your account is active. You can
            delete chains and associated entries at any time through the
            dashboard or API. Data will be retained for 30 days after account
            closure.
          </p>

          <h2>5. Data security</h2>
          <p>
            We protect your data with TLS 1.3 in transit, AES-256-GCM at rest,
            and SHA-256 hashed API keys. See our{" "}
            <a href="/security">Security page</a> for complete details.
          </p>

          <h2>6. Third-party services</h2>
          <p>
            We do not sell your personal information. We may share information
            with third-party service providers who assist us in operating the
            Service, subject to contractual obligations to protect your data. We
            may disclose information if required by law.
          </p>

          <h2>7. Your rights</h2>
          <p>
            Depending on your jurisdiction (GDPR, CCPA), you may have the right
            to access, correct, delete, or port your personal data. You may also
            have the right to restrict or object to certain processing. To
            exercise these rights, contact{" "}
            <a href="mailto:privacy@pruv.dev">privacy@pruv.dev</a>.
          </p>

          <h2>8. Contact</h2>
          <p>
            For privacy-related questions, contact{" "}
            <a href="mailto:privacy@pruv.dev">privacy@pruv.dev</a>.
          </p>
        </div>
      </div>
    </div>
  );
}
