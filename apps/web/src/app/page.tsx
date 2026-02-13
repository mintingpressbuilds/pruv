"use client";

import { motion } from "framer-motion";
import { Hero } from "@/components/hero";
import { CodeBlock } from "@/components/code-block";
import { ComparisonTable } from "@/components/comparison-table";
import { CtaSection } from "@/components/cta-section";

const industries = [
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
      </svg>
    ),
    title: "AI & Agents",
    description: "Prove what autonomous agents actually did",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 14.25h13.5m-13.5 0a3 3 0 01-3-3m3 3a3 3 0 100 6h13.5a3 3 0 100-6m-16.5-3a3 3 0 013-3h13.5a3 3 0 013 3m-19.5 0a4.5 4.5 0 01.9-2.7L5.737 5.1a3.375 3.375 0 012.7-1.35h7.126c1.062 0 2.062.5 2.7 1.35l2.587 3.45a4.5 4.5 0 01.9 2.7m0 0a3 3 0 01-3 3m0 3h.008v.008h-.008v-.008zm0-6h.008v.008h-.008v-.008zm-3 6h.008v.008h-.008v-.008zm0-6h.008v.008h-.008v-.008z" />
      </svg>
    ),
    title: "DevOps",
    description: "Verify every deploy, change, and rollback",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
      </svg>
    ),
    title: "Finance",
    description: "Tamper-proof transaction audit trails",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
      </svg>
    ),
    title: "Healthcare",
    description: "Patient record chain of custody",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.332A48.36 48.36 0 0012 9.75c-2.551 0-5.056.2-7.5.582V21M3 21h18M12 6.75h.008v.008H12V6.75z" />
      </svg>
    ),
    title: "Government",
    description: "Public records transparency",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 18.75a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 01-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h1.125c.621 0 1.129-.504 1.09-1.124a17.902 17.902 0 00-3.213-9.193 2.056 2.056 0 00-1.58-.86H14.25M16.5 18.75h-2.25m0-11.177v-.958c0-.568-.422-1.048-.987-1.106a48.554 48.554 0 00-10.026 0 1.106 1.106 0 00-.987 1.106v7.635m12-6.677v6.677m0 4.5v-4.5m0 0h-12" />
      </svg>
    ),
    title: "Supply Chain",
    description: "End-to-end provenance tracking",
  },
];

const installCode = `$ pip install pruv`;

const usageCode = `from pruv import xy_wrap

# Wrap any state transition
@xy_wrap
def deploy_service(config: dict) -> dict:
    # X = config (before state)
    result = kubernetes.apply(config)
    return result
    # Y = result (after state)
    # XY = cryptographic proof of X -> Y

# Every call is now a verifiable record
deploy_service({"image": "api:v2.1.0", "replicas": 3})

# Later: verify what actually happened
from pruv import verify
proof = verify("deploy_service", entry_id="xy_8f3a...")
assert proof.valid  # cryptographic guarantee`;

export default function HomePage() {
  return (
    <>
      {/* Hero */}
      <Hero />

      {/* Install */}
      <section id="install" className="section-padding pt-12 pb-16">
        <div className="container-narrow">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.5 }}
            className="max-w-md mx-auto"
          >
            <CodeBlock code={installCode} language="bash" />
          </motion.div>
        </div>
      </section>

      {/* Works Everywhere */}
      <section className="section-padding pt-8">
        <div className="container-wide">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.5 }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">
              Works everywhere.
            </h2>
            <p className="mt-4 text-lg text-zinc-400">
              From AI agents to financial systems, pruv adds cryptographic proof
              to any state transition.
            </p>
          </motion.div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {industries.map((industry, i) => (
              <motion.div
                key={industry.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.06 }}
                className="group p-5 rounded-2xl bg-zinc-900/50 border border-zinc-800 hover:border-emerald-500/30 transition-all text-center cursor-default"
              >
                <div className="w-12 h-12 mx-auto rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-3 group-hover:bg-emerald-500/20 transition-colors">
                  {industry.icon}
                </div>
                <h3 className="text-sm font-semibold text-white">
                  {industry.title}
                </h3>
                <p className="mt-1 text-xs text-zinc-500">
                  {industry.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="section-padding">
        <div className="container-narrow">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.5 }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">
              The XY primitive.
            </h2>
            <p className="mt-4 text-lg text-zinc-400 max-w-2xl mx-auto">
              Every system transforms state. pruv captures the before (X), the
              after (Y), and generates a cryptographic proof (XY) that the
              transition occurred.
            </p>
          </motion.div>

          {/* Animated diagram */}
          <div className="relative flex flex-col sm:flex-row items-center justify-center gap-6 sm:gap-4 p-8 sm:p-12 rounded-3xl bg-zinc-900/30 border border-zinc-800">
            {/* Step 1: X */}
            <motion.div
              initial={{ opacity: 0, x: -40 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.6, delay: 0 }}
              className="flex flex-col items-center"
            >
              <div className="w-24 h-24 rounded-2xl bg-zinc-800 border border-zinc-700 flex items-center justify-center mb-3">
                <span className="font-mono text-4xl font-bold text-zinc-300">
                  X
                </span>
              </div>
              <span className="text-sm font-medium text-zinc-400">Before</span>
              <span className="text-xs text-zinc-600 mt-1">
                Capture initial state
              </span>
            </motion.div>

            {/* Arrow 1 */}
            <motion.div
              initial={{ scaleX: 0, opacity: 0 }}
              whileInView={{ scaleX: 1, opacity: 1 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="flex items-center origin-left"
            >
              <div className="w-12 sm:w-20 h-0.5 bg-gradient-to-r from-zinc-600 to-emerald-500" />
              <svg
                className="w-5 h-5 text-emerald-500 -ml-1"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={2}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3"
                />
              </svg>
            </motion.div>

            {/* Step 2: Y */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.6, delay: 0.5 }}
              className="flex flex-col items-center"
            >
              <div className="w-24 h-24 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center mb-3">
                <span className="font-mono text-4xl font-bold text-emerald-400">
                  Y
                </span>
              </div>
              <span className="text-sm font-medium text-emerald-400">
                After
              </span>
              <span className="text-xs text-zinc-600 mt-1">
                Record final state
              </span>
            </motion.div>

            {/* Arrow 2 */}
            <motion.div
              initial={{ scaleX: 0, opacity: 0 }}
              whileInView={{ scaleX: 1, opacity: 1 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.5, delay: 0.7 }}
              className="flex items-center origin-left"
            >
              <div className="w-8 sm:w-14 h-0.5 bg-gradient-to-r from-emerald-500 to-emerald-300" />
              <span className="text-emerald-400 font-mono text-sm ml-1">
                =
              </span>
            </motion.div>

            {/* Step 3: XY */}
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.6, delay: 0.9 }}
              className="flex flex-col items-center"
            >
              <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-emerald-500/5 border border-emerald-500/40 flex items-center justify-center mb-3 glow">
                <span className="font-mono text-3xl font-bold text-emerald-300">
                  XY
                </span>
              </div>
              <span className="text-sm font-medium gradient-text">Proof</span>
              <span className="text-xs text-zinc-600 mt-1">
                Verifiable record
              </span>
            </motion.div>
          </div>

          {/* Chain rule explanation */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="mt-8 p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800"
          >
            <h3 className="text-sm font-semibold text-zinc-300 mb-2">
              The chain rule
            </h3>
            <p className="text-sm text-zinc-500">
              When Y of one transition becomes X of the next, pruv links them
              cryptographically. This creates an unbreakable chain of custody
              across any number of state transitions:{" "}
              <span className="font-mono text-emerald-400">
                X1Y1 &rarr; X2Y2 &rarr; X3Y3 &rarr; ...
              </span>
            </p>
          </motion.div>
        </div>
      </section>

      {/* Code Example */}
      <section className="section-padding pt-8">
        <div className="container-narrow">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.5 }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">
              Two lines of code.
            </h2>
            <p className="mt-4 text-lg text-zinc-400 max-w-2xl mx-auto">
              Import pruv. Decorate your function. Every call is now a
              cryptographically verifiable record.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.6 }}
          >
            <CodeBlock
              code={usageCode}
              language="python"
              filename="deploy.py"
              showLineNumbers
            />
          </motion.div>
        </div>
      </section>

      {/* Comparison Table */}
      <section className="section-padding">
        <div className="container-narrow">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.5 }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">
              Not logging. Proof.
            </h2>
            <p className="mt-4 text-lg text-zinc-400 max-w-2xl mx-auto">
              Logs tell you what someone said happened. pruv proves what
              actually happened.
            </p>
          </motion.div>

          <ComparisonTable />
        </div>
      </section>

      {/* CTA */}
      <CtaSection
        title="Start proving."
        subtitle="Add verifiable proof to your system in under five minutes. Free for up to 1,000 entries per month."
        primaryCta="Get Started Free"
        secondaryCta="View Pricing"
        secondaryHref="/pricing"
      />
    </>
  );
}
