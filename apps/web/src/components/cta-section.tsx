"use client";

import { motion } from "framer-motion";

interface CtaSectionProps {
  title?: string;
  subtitle?: string;
  primaryCta?: string;
  primaryHref?: string;
  secondaryCta?: string;
  secondaryHref?: string;
}

export function CtaSection({
  title = "Start proving.",
  subtitle = "Add cryptographic verification to your system in minutes.",
  primaryCta = "Get Started Free",
  primaryHref = "#",
  secondaryCta = "Read the Docs",
  secondaryHref = "https://docs.pruv.dev",
}: CtaSectionProps) {
  return (
    <section className="section-padding">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-50px" }}
        transition={{ duration: 0.6 }}
        className="container-narrow text-center"
      >
        <div className="relative rounded-3xl overflow-hidden p-12 sm:p-16 lg:p-20">
          {/* Background */}
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 via-transparent to-emerald-500/5 border border-emerald-500/20 rounded-3xl" />
          <div className="absolute inset-0 bg-[linear-gradient(rgba(16,185,129,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(16,185,129,0.02)_1px,transparent_1px)] bg-[size:32px_32px]" />

          <div className="relative">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight">
              {title}
            </h2>
            <p className="mt-4 text-lg text-zinc-400 max-w-xl mx-auto">
              {subtitle}
            </p>
            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
              <a
                href={primaryHref}
                className="px-8 py-3.5 text-sm font-medium bg-emerald-500 hover:bg-emerald-400 text-black rounded-xl transition-all hover:shadow-[0_0_30px_rgba(16,185,129,0.3)]"
              >
                {primaryCta}
              </a>
              <a
                href={secondaryHref}
                className="px-8 py-3.5 text-sm font-medium text-zinc-300 border border-zinc-700 hover:border-zinc-500 rounded-xl transition-colors"
              >
                {secondaryCta}
              </a>
            </div>
          </div>
        </div>
      </motion.div>
    </section>
  );
}
