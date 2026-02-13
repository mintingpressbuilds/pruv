"use client";

import { motion } from "framer-motion";

export default function TermsPage() {
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
              Terms of Service
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
                1. Acceptance of Terms
              </h2>
              <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800">
                <p className="text-zinc-400 leading-relaxed">
                  By accessing or using pruv (the &quot;Service&quot;), including
                  the xycore library, pruv SDK, cloud API, dashboard, and
                  documentation, you agree to be bound by these Terms of Service.
                  If you do not agree, do not use the Service.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">
                2. Service Description
              </h2>
              <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800">
                <p className="text-zinc-400 leading-relaxed">
                  pruv provides cryptographic verification infrastructure for
                  state transitions. The Service includes chain storage,
                  verification, receipt generation, digital signatures,
                  auto-redaction, and related features as described in our
                  documentation at docs.pruv.dev.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">
                3. Usage Limits
              </h2>
              <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800 space-y-4">
                <p className="text-zinc-400 leading-relaxed">
                  Each plan has specific rate limits and monthly entry quotas:
                </p>
                <ul className="space-y-2">
                  {[
                    "Free: 60 requests/min, 1,000 entries/month",
                    "Pro: 300 requests/min, 50,000 entries/month",
                    "Team: 1,000 requests/min, 500,000 entries/month",
                    "Enterprise: custom limits per agreement",
                  ].map((item) => (
                    <li
                      key={item}
                      className="flex items-start gap-3 text-sm text-zinc-400"
                    >
                      <span className="text-emerald-400 mt-1">&bull;</span>
                      {item}
                    </li>
                  ))}
                </ul>
                <p className="text-zinc-400 leading-relaxed">
                  Exceeding your quota will result in entries being queued until
                  your limit resets. We will notify you at 80% and 100% usage.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">
                4. API Keys and Security
              </h2>
              <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800">
                <p className="text-zinc-400 leading-relaxed">
                  You are responsible for keeping your API keys secure. API keys
                  with the{" "}
                  <span className="font-mono text-emerald-400">pv_live_</span>{" "}
                  prefix provide production access. Keys with the{" "}
                  <span className="font-mono text-emerald-400">pv_test_</span>{" "}
                  prefix provide testing access. Compromised keys should be
                  revoked immediately through the dashboard. You are responsible
                  for all activity that occurs under your API keys.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">
                5. Data Ownership
              </h2>
              <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800">
                <p className="text-zinc-400 leading-relaxed">
                  You retain full ownership of all data submitted to pruv. We do
                  not claim ownership of your chains, entries, or associated
                  state data. We will not access, use, or disclose your data
                  except as necessary to provide the Service, as required by law,
                  or with your explicit consent.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">
                6. Open Source
              </h2>
              <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800">
                <p className="text-zinc-400 leading-relaxed">
                  The xycore package is released under the MIT License. The pruv
                  SDK is released under the MIT License. Use of the cloud service
                  (api.pruv.dev) is governed by these Terms. The open source
                  licenses apply only to the software itself, not to the hosted
                  service.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">
                7. Service Level
              </h2>
              <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800">
                <p className="text-zinc-400 leading-relaxed">
                  Team and Enterprise plans include a Service Level Agreement
                  (SLA) with guaranteed uptime. Free and Pro plans are provided
                  on a best-effort basis. We strive for high availability but do
                  not guarantee specific uptime for non-SLA plans.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">
                8. Termination
              </h2>
              <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800">
                <p className="text-zinc-400 leading-relaxed">
                  Either party may terminate at any time. Upon termination, you
                  may export your data via the API or CLI. Data will be retained
                  for 30 days after account closure, after which it will be
                  permanently deleted.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">
                9. Limitation of Liability
              </h2>
              <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800">
                <p className="text-zinc-400 leading-relaxed">
                  To the maximum extent permitted by applicable law, pruv shall
                  not be liable for any indirect, incidental, special,
                  consequential, or punitive damages, or any loss of profits or
                  revenues. Our total liability shall not exceed the amount you
                  paid us in the twelve months preceding the claim.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">
                10. Contact
              </h2>
              <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800">
                <p className="text-zinc-400 leading-relaxed">
                  For questions about these Terms of Service, contact us at{" "}
                  <a
                    href="mailto:legal@pruv.dev"
                    className="text-emerald-400 hover:text-emerald-300"
                  >
                    legal@pruv.dev
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
