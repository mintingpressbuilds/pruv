"use client";

import { motion } from "framer-motion";

export default function PrivacyPage() {
  return (
    <div className="pt-24">
      <section className="section-padding">
        <div className="container-narrow">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mb-16"
          >
            <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">
              Privacy Policy
            </h1>
            <p className="mt-4 text-zinc-500">
              Last updated: January 15, 2025
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="space-y-10"
          >
            <section>
              <h2 className="text-2xl font-bold text-white mb-4">
                1. Introduction
              </h2>
              <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800 space-y-4">
                <p className="text-zinc-400 leading-relaxed">
                  pruv (&quot;we,&quot; &quot;our,&quot; or &quot;us&quot;) is
                  committed to protecting your privacy. This Privacy Policy
                  explains how we collect, use, disclose, and safeguard your
                  information when you use the pruv platform, API, SDK, and
                  website (collectively, the &quot;Service&quot;).
                </p>
                <p className="text-zinc-400 leading-relaxed">
                  By using the Service, you agree to the collection and use of
                  information in accordance with this policy.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">
                2. Information We Collect
              </h2>
              <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800 space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-white mb-2">
                    Account Information
                  </h3>
                  <p className="text-zinc-400 leading-relaxed">
                    When you create an account, we collect your email address,
                    name, and authentication credentials. If you sign up via
                    OAuth (GitHub, Google), we receive your profile information
                    from the provider.
                  </p>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white mb-2">
                    Verification Data
                  </h3>
                  <p className="text-zinc-400 leading-relaxed">
                    When you use the pruv SDK or API, we receive XY records
                    containing hashed state data. By default, pruv transmits
                    only cryptographic hashes of your data, not the raw data
                    itself. If you choose to store full state snapshots, that
                    data is encrypted at rest with AES-256-GCM.
                  </p>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white mb-2">
                    Auto-Redaction
                  </h3>
                  <p className="text-zinc-400 leading-relaxed">
                    pruv automatically redacts detected secrets (API keys,
                    passwords, tokens) before storing chain data. This feature is
                    enabled by default and can be controlled via the
                    PRUV_AUTO_REDACT environment variable.
                  </p>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white mb-2">
                    Usage Data
                  </h3>
                  <p className="text-zinc-400 leading-relaxed">
                    We collect information about how you interact with the
                    Service, including API call frequency, feature usage, and
                    error rates. This data is used to improve the Service and is
                    not sold to third parties.
                  </p>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">
                3. How We Use Your Information
              </h2>
              <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800">
                <ul className="space-y-3">
                  {[
                    "Provide, maintain, and improve the Service",
                    "Store and verify your XY chains and generate receipts",
                    "Process transactions and send related information",
                    "Send technical notices, updates, and security alerts",
                    "Respond to your comments, questions, and support requests",
                    "Monitor and analyze trends, usage, and activities",
                    "Detect, investigate, and prevent fraudulent or unauthorized activity",
                  ].map((item) => (
                    <li
                      key={item}
                      className="flex items-start gap-3 text-zinc-400"
                    >
                      <svg
                        className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth={2}
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M4.5 12.75l6 6 9-13.5"
                        />
                      </svg>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">
                4. Data Retention
              </h2>
              <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800">
                <p className="text-zinc-400 leading-relaxed">
                  Verification records are retained according to your plan: Free
                  (7 days), Pro (90 days), Team (1 year), Enterprise (custom).
                  Account information is retained as long as your account is
                  active. You can delete chains and associated entries at any
                  time through the dashboard or API. Data will be retained for 30
                  days after account closure.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">
                5. Data Security
              </h2>
              <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800">
                <p className="text-zinc-400 leading-relaxed">
                  We protect your data with TLS 1.3 in transit, AES-256-GCM at
                  rest, and SHA-256 hashed API keys. See our{" "}
                  <a
                    href="/security"
                    className="text-emerald-400 hover:text-emerald-300"
                  >
                    Security page
                  </a>{" "}
                  for complete details on our security practices.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">
                6. Third-Party Services
              </h2>
              <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800">
                <p className="text-zinc-400 leading-relaxed">
                  We do not sell your personal information. We may share
                  information with third-party service providers who assist us in
                  operating the Service, subject to contractual obligations to
                  protect your data. We may disclose information if required by
                  law or to protect our rights.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">
                7. Your Rights
              </h2>
              <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800">
                <p className="text-zinc-400 leading-relaxed">
                  Depending on your jurisdiction (GDPR, CCPA), you may have the
                  right to access, correct, delete, or port your personal data.
                  You may also have the right to restrict or object to certain
                  processing. To exercise these rights, contact us at{" "}
                  <a
                    href="mailto:privacy@pruv.dev"
                    className="text-emerald-400 hover:text-emerald-300"
                  >
                    privacy@pruv.dev
                  </a>
                  .
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">
                8. Contact
              </h2>
              <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800">
                <p className="text-zinc-400 leading-relaxed">
                  For privacy-related questions, contact us at{" "}
                  <a
                    href="mailto:privacy@pruv.dev"
                    className="text-emerald-400 hover:text-emerald-300"
                  >
                    privacy@pruv.dev
                  </a>
                  .
                </p>
              </div>
            </section>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
