"use client";

import { motion } from "framer-motion";

export function Hero() {
  return (
    <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden pt-16">
      {/* Background grid */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(16,185,129,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(16,185,129,0.03)_1px,transparent_1px)] bg-[size:64px_64px]" />

      {/* Radial glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] bg-emerald-500/5 rounded-full blur-3xl" />

      <div className="relative max-w-5xl mx-auto px-4 sm:px-6 text-center">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            v1.0 is live
          </span>
        </motion.div>

        {/* X -> Y */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.1 }}
          className="mt-8"
        >
          <div className="flex items-center justify-center gap-3 sm:gap-6 mb-6">
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="w-16 h-16 sm:w-24 sm:h-24 rounded-2xl bg-zinc-800 border border-zinc-700 flex items-center justify-center"
            >
              <span className="font-mono text-3xl sm:text-5xl font-bold text-zinc-300">
                X
              </span>
            </motion.div>

            <motion.div
              initial={{ scaleX: 0, opacity: 0 }}
              animate={{ scaleX: 1, opacity: 1 }}
              transition={{ duration: 0.4, delay: 0.5 }}
              className="flex items-center"
            >
              <div className="w-8 sm:w-16 h-0.5 bg-gradient-to-r from-zinc-600 to-emerald-500" />
              <svg
                className="w-4 h-4 sm:w-6 sm:h-6 text-emerald-500 -ml-1"
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

            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.6 }}
              className="w-16 h-16 sm:w-24 sm:h-24 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center glow"
            >
              <span className="font-mono text-3xl sm:text-5xl font-bold text-emerald-400">
                Y
              </span>
            </motion.div>
          </div>
        </motion.div>

        {/* Tagline */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.4 }}
          className="text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-balance"
        >
          Prove what happened.
        </motion.h1>

        {/* Sub-tagline */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.5 }}
          className="mt-6 text-lg sm:text-xl text-zinc-400 max-w-2xl mx-auto text-balance"
        >
          Cryptographic verification for any system.
        </motion.p>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.6 }}
          className="mt-3 text-base text-zinc-500 max-w-2xl mx-auto"
        >
          Record the before. Record the after. Generate proof that it happened.
          Every X&nbsp;&rarr;&nbsp;Y transition becomes a verifiable, tamper-evident
          record.
        </motion.p>

        {/* CTA buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.7 }}
          className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <a
            href="#install"
            className="px-8 py-3.5 text-sm font-medium bg-emerald-500 hover:bg-emerald-400 text-black rounded-xl transition-all hover:shadow-[0_0_30px_rgba(16,185,129,0.3)]"
          >
            Get Started
          </a>
          <a
            href="/how-it-works"
            className="px-8 py-3.5 text-sm font-medium text-zinc-300 border border-zinc-700 hover:border-zinc-500 rounded-xl transition-colors"
          >
            How It Works
          </a>
        </motion.div>
      </div>
    </section>
  );
}
