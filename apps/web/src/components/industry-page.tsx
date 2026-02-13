"use client";

import { motion } from "framer-motion";
import { CodeBlock } from "./code-block";
import { CtaSection } from "./cta-section";

interface UseCase {
  title: string;
  description: string;
}

interface IndustryPageProps {
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  problem: {
    title: string;
    description: string;
    points: string[];
  };
  solution: {
    title: string;
    description: string;
    xLabel: string;
    yLabel: string;
    example: string;
  };
  codeExample: {
    code: string;
    filename: string;
  };
  useCases: UseCase[];
}

export function IndustryPage({
  icon,
  title,
  subtitle,
  problem,
  solution,
  codeExample,
  useCases,
}: IndustryPageProps) {
  return (
    <div className="pt-24">
      {/* Hero */}
      <section className="section-padding pb-12">
        <div className="container-narrow">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="flex items-center gap-3 mb-6"
          >
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              {icon}
            </div>
            <span className="text-sm text-emerald-400 font-medium">
              Industry
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight"
          >
            {title}
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mt-6 text-xl text-zinc-400 max-w-3xl"
          >
            {subtitle}
          </motion.p>
        </div>
      </section>

      {/* Problem */}
      <section className="section-padding pt-12">
        <div className="container-narrow">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-2xl sm:text-3xl font-bold mb-4">
              {problem.title}
            </h2>
            <p className="text-zinc-400 text-lg mb-8 max-w-3xl">
              {problem.description}
            </p>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {problem.points.map((point, i) => (
                <motion.div
                  key={point}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: i * 0.1 }}
                  className="p-4 rounded-xl bg-red-500/5 border border-red-500/10"
                >
                  <div className="flex items-start gap-3">
                    <svg
                      className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5"
                      fill="none"
                      viewBox="0 0 24 24"
                      strokeWidth={2}
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
                      />
                    </svg>
                    <span className="text-sm text-zinc-300">{point}</span>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Solution / X -> Y */}
      <section className="section-padding">
        <div className="container-narrow">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-2xl sm:text-3xl font-bold mb-4">
              {solution.title}
            </h2>
            <p className="text-zinc-400 text-lg mb-10 max-w-3xl">
              {solution.description}
            </p>

            {/* X -> Y Diagram */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-6 p-8 rounded-2xl bg-zinc-900/50 border border-zinc-800">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: 0.1 }}
                className="text-center"
              >
                <div className="w-20 h-20 rounded-2xl bg-zinc-800 border border-zinc-700 flex items-center justify-center mb-2">
                  <span className="font-mono text-3xl font-bold text-zinc-300">
                    X
                  </span>
                </div>
                <p className="text-xs text-zinc-500 max-w-[120px]">
                  {solution.xLabel}
                </p>
              </motion.div>

              <motion.div
                initial={{ scaleX: 0 }}
                whileInView={{ scaleX: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: 0.3 }}
                className="flex items-center"
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

              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: 0.5 }}
                className="text-center"
              >
                <div className="w-20 h-20 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center mb-2 glow-sm">
                  <span className="font-mono text-3xl font-bold text-emerald-400">
                    Y
                  </span>
                </div>
                <p className="text-xs text-zinc-500 max-w-[120px]">
                  {solution.yLabel}
                </p>
              </motion.div>

              <motion.div
                initial={{ scaleX: 0 }}
                whileInView={{ scaleX: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: 0.7 }}
                className="flex items-center"
              >
                <div className="w-8 sm:w-12 h-0.5 bg-gradient-to-r from-emerald-500 to-emerald-300" />
                <span className="text-emerald-400 font-mono text-xs ml-1">
                  =
                </span>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: 0.9 }}
                className="text-center"
              >
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-emerald-500/5 border border-emerald-500/40 flex items-center justify-center mb-2 glow">
                  <span className="font-mono text-2xl font-bold text-emerald-300">
                    XY
                  </span>
                </div>
                <p className="text-xs text-zinc-500 max-w-[120px]">
                  Verifiable proof
                </p>
              </motion.div>
            </div>

            <p className="mt-6 text-sm text-zinc-500 text-center italic">
              {solution.example}
            </p>
          </motion.div>
        </div>
      </section>

      {/* Code Example */}
      <section className="section-padding pt-8">
        <div className="container-narrow">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-2xl sm:text-3xl font-bold mb-2">
              Code Example
            </h2>
            <p className="text-zinc-400 mb-8">
              See how pruv integrates into your workflow.
            </p>
            <CodeBlock
              code={codeExample.code}
              language="python"
              filename={codeExample.filename}
              showLineNumbers
            />
          </motion.div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="section-padding">
        <div className="container-narrow">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-2xl sm:text-3xl font-bold mb-10"
          >
            Use Cases
          </motion.h2>

          <div className="grid sm:grid-cols-2 gap-6">
            {useCases.map((uc, i) => (
              <motion.div
                key={uc.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.1 }}
                className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800 hover:border-emerald-500/20 transition-colors"
              >
                <h3 className="text-lg font-semibold text-white mb-2">
                  {uc.title}
                </h3>
                <p className="text-sm text-zinc-400 leading-relaxed">
                  {uc.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <CtaSection />
    </div>
  );
}
