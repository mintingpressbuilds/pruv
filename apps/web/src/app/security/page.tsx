"use client";

import { motion } from "framer-motion";

const protections = [
  {
    layer: "In Transit",
    method: "TLS 1.3",
    description:
      "All data in transit is encrypted with TLS 1.3. HSTS is enforced. Certificate transparency is monitored.",
  },
  {
    layer: "At Rest",
    method: "AES-256-GCM",
    description:
      "All stored data is encrypted with AES-256-GCM. Encryption keys are rotated regularly and managed via a dedicated KMS.",
  },
  {
    layer: "Hashing",
    method: "SHA-256",
    description:
      "All XY proofs use SHA-256 for content hashing. State is canonicalized before hashing to ensure deterministic results.",
  },
  {
    layer: "Signatures",
    method: "Ed25519",
    description:
      "Optional Ed25519 digital signatures provide non-repudiation. Signers cannot deny having created an entry. Signatures can be verified independently.",
  },
  {
    layer: "API Keys",
    method: "SHA-256 hashed",
    description:
      "API keys are SHA-256 hashed before storage. We never store API keys in plaintext. Keys use the pv_live_ and pv_test_ prefix convention.",
  },
  {
    layer: "Secrets",
    method: "Auto-redacted",
    description:
      "Sensitive data is automatically detected and redacted before it enters the chain. Proofs remain valid even after redaction.",
  },
];

const redactionPatterns = [
  { pattern: "sk_live_*, sk_test_*", service: "Stripe API keys" },
  { pattern: "pv_live_*, pv_test_*", service: "pruv API keys" },
  { pattern: "ghp_*, gho_*, ghs_*", service: "GitHub tokens" },
  { pattern: "AKIA*", service: "AWS access keys" },
  {
    pattern: "password, secret, token, api_key",
    service: "Generic secret fields",
  },
  { pattern: "SSN, credit_card, cvv", service: "PII and financial data" },
];

export default function SecurityPage() {
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
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight">
              Security
            </h1>
            <p className="mt-6 text-xl text-zinc-400 max-w-3xl">
              How pruv protects your data and ensures the integrity of
              verification records. Security is not a feature. It is the
              foundation.
            </p>
          </motion.div>

          {/* Cryptographic verification */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.5 }}
            className="mb-16"
          >
            <h2 className="text-2xl sm:text-3xl font-bold mb-6">
              Cryptographic Verification
            </h2>
            <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800">
              <p className="text-zinc-400 leading-relaxed mb-4">
                pruv uses SHA-256 hashing to create tamper-evident chains of
                state transitions. Every entry&apos;s XY proof hash is computed
                from the canonical representation of the before state (X) and
                after state (Y), combined with metadata including the timestamp
                and the hash of the previous entry in the chain.
              </p>
              <p className="text-zinc-400 leading-relaxed mb-4">
                The chain rule ensures that{" "}
                <span className="font-mono text-emerald-400">
                  Entry[N].x == Entry[N-1].y
                </span>
                . Any modification to any entry in the chain invalidates all
                subsequent hashes, making tampering mathematically detectable.
              </p>
              <p className="text-zinc-400 leading-relaxed">
                Verification is independent: anyone with the XY records can
                verify the entire chain using standard SHA-256 libraries. No
                proprietary tools are required.
              </p>
            </div>
          </motion.div>

          {/* Data protection table */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.5 }}
            className="mb-16"
          >
            <h2 className="text-2xl sm:text-3xl font-bold mb-6">
              Data Protection
            </h2>
            <div className="space-y-4">
              {protections.map((item, i) => (
                <motion.div
                  key={item.layer}
                  initial={{ opacity: 0, y: 15 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.3, delay: i * 0.05 }}
                  className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800"
                >
                  <div className="flex flex-wrap items-center gap-3 mb-2">
                    <h3 className="font-semibold text-white">{item.layer}</h3>
                    <span className="px-2 py-0.5 text-xs font-mono bg-emerald-500/10 text-emerald-400 rounded border border-emerald-500/20">
                      {item.method}
                    </span>
                  </div>
                  <p className="text-sm text-zinc-400">{item.description}</p>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Auto-redaction */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.5 }}
            className="mb-16"
          >
            <h2 className="text-2xl sm:text-3xl font-bold mb-6">
              Auto-Redaction
            </h2>
            <p className="text-zinc-400 mb-6">
              pruv automatically detects and redacts sensitive data before it
              enters the verification chain. Redacted values are replaced with
              hash commitments, so the proof remains verifiable even after
              sensitive content is removed.
            </p>
            <div className="overflow-x-auto rounded-2xl border border-zinc-800">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-zinc-800 bg-zinc-900/50">
                    <th className="text-left py-3 px-4 text-zinc-500 font-medium">
                      Pattern
                    </th>
                    <th className="text-left py-3 px-4 text-zinc-500 font-medium">
                      Service
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {redactionPatterns.map((rp) => (
                    <tr
                      key={rp.pattern}
                      className="border-b border-zinc-800/50"
                    >
                      <td className="py-3 px-4 font-mono text-xs text-emerald-400">
                        {rp.pattern}
                      </td>
                      <td className="py-3 px-4 text-zinc-300">{rp.service}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>

          {/* Infrastructure */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.5 }}
            className="mb-16"
          >
            <h2 className="text-2xl sm:text-3xl font-bold mb-6">
              Infrastructure
            </h2>
            <div className="grid sm:grid-cols-2 gap-4">
              {[
                {
                  title: "DDoS Protection",
                  description:
                    "All traffic is routed through Cloudflare for DDoS mitigation, WAF, and CDN.",
                },
                {
                  title: "Rate Limiting",
                  description:
                    "Sliding window rate limiting on all API endpoints to prevent abuse.",
                },
                {
                  title: "SOC 2 Type II",
                  description:
                    "pruv infrastructure follows SOC 2 Type II controls for security, availability, and confidentiality.",
                },
                {
                  title: "Penetration Testing",
                  description:
                    "Regular third-party penetration testing and security audits.",
                },
              ].map((item) => (
                <div
                  key={item.title}
                  className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800"
                >
                  <h3 className="font-semibold text-white mb-2">
                    {item.title}
                  </h3>
                  <p className="text-sm text-zinc-400">{item.description}</p>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Responsible disclosure */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-2xl sm:text-3xl font-bold mb-6">
              Responsible Disclosure
            </h2>
            <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800">
              <p className="text-zinc-400 leading-relaxed">
                If you discover a security vulnerability in pruv, please report
                it responsibly. Email{" "}
                <a
                  href="mailto:security@pruv.dev"
                  className="text-emerald-400 hover:text-emerald-300"
                >
                  security@pruv.dev
                </a>{" "}
                with details of the vulnerability. We aim to acknowledge reports
                within 24 hours and provide a fix within 72 hours for critical
                issues.
              </p>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
