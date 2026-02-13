"use client";

import { motion } from "framer-motion";

const releases = [
  {
    version: "1.0.0",
    date: "2025-01-15",
    title: "Initial Release",
    description: "pruv is live. Cryptographic verification for any system.",
    sections: [
      {
        label: "xycore",
        description: "The XY primitive. Zero dependencies.",
        items: [
          "XYEntry, XYChain, and XYReceipt data structures",
          "hash_state() and compute_xy() cryptographic hash functions",
          "verify_entry() and verify_chain() for independent verification",
          "Ed25519 digital signatures for non-repudiation",
          "Auto-redaction of secrets and sensitive data",
          "LocalStorage backend for JSON file persistence",
        ],
      },
      {
        label: "pruv SDK",
        description: "Full platform SDK for Python.",
        items: [
          "Scanner with automatic framework and service detection",
          "xy_wrap() universal decorator for any function",
          "CheckpointManager with restore and undo",
          "ApprovalGate for human-in-the-loop workflows",
          "CloudClient with offline queue and background sync",
          "CLI: scan, verify, export, undo, upload commands",
        ],
      },
      {
        label: "Platform",
        description: "API, dashboard, and marketing site.",
        items: [
          "FastAPI backend at api.pruv.dev",
          "Next.js dashboard at app.pruv.dev",
          "Marketing site at pruv.dev",
          "Documentation at docs.pruv.dev",
          "Free tier: 1,000 entries per month",
        ],
      },
    ],
  },
];

export default function ChangelogPage() {
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
              Changelog
            </h1>
            <p className="mt-6 text-xl text-zinc-400">
              All notable changes to the pruv platform.
            </p>
          </motion.div>

          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-4 top-0 bottom-0 w-px bg-zinc-800" />

            {releases.map((release, ri) => (
              <motion.div
                key={release.version}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.5 }}
                className="relative pl-12 pb-16"
              >
                {/* Timeline dot */}
                <div className="absolute left-2 top-1 w-5 h-5 rounded-full bg-emerald-500 border-4 border-zinc-950" />

                {/* Header */}
                <div className="flex flex-wrap items-center gap-3 mb-4">
                  <span className="px-3 py-1 text-sm font-mono font-medium bg-emerald-500/10 text-emerald-400 rounded-full border border-emerald-500/20">
                    v{release.version}
                  </span>
                  <span className="text-sm text-zinc-500">{release.date}</span>
                </div>

                <h2 className="text-2xl font-bold text-white mb-2">
                  {release.title}
                </h2>
                <p className="text-zinc-400 mb-8">{release.description}</p>

                {/* Sections */}
                <div className="space-y-8">
                  {release.sections.map((section) => (
                    <div
                      key={section.label}
                      className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800"
                    >
                      <div className="flex items-center gap-3 mb-2">
                        <span className="font-mono font-semibold text-white">
                          {section.label}
                        </span>
                      </div>
                      <p className="text-sm text-zinc-500 mb-4">
                        {section.description}
                      </p>
                      <ul className="space-y-2">
                        {section.items.map((item) => (
                          <li
                            key={item}
                            className="flex items-start gap-2 text-sm text-zinc-300"
                          >
                            <svg
                              className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5"
                              fill="none"
                              viewBox="0 0 24 24"
                              strokeWidth={2}
                              stroke="currentColor"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                d="M12 4.5v15m7.5-7.5h-15"
                              />
                            </svg>
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
