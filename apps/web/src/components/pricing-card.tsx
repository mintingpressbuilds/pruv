"use client";

import { motion } from "framer-motion";

interface PricingCardProps {
  name: string;
  price: string;
  period?: string;
  description: string;
  features: string[];
  highlighted?: boolean;
  cta: string;
  index: number;
}

export function PricingCard({
  name,
  price,
  period,
  description,
  features,
  highlighted = false,
  cta,
  index,
}: PricingCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className={`relative rounded-2xl p-8 flex flex-col ${
        highlighted
          ? "bg-emerald-500/5 border-2 border-emerald-500/30 glow"
          : "bg-zinc-900/50 border border-zinc-800"
      }`}
    >
      {highlighted && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <span className="px-3 py-1 text-xs font-medium bg-emerald-500 text-black rounded-full">
            Most Popular
          </span>
        </div>
      )}

      <div className="mb-6">
        <h3 className="text-lg font-semibold text-white">{name}</h3>
        <p className="mt-1 text-sm text-zinc-500">{description}</p>
      </div>

      <div className="mb-6">
        <span className="text-4xl font-bold text-white">{price}</span>
        {period && <span className="text-zinc-500 ml-1">{period}</span>}
      </div>

      <ul className="space-y-3 mb-8 flex-1">
        {features.map((feature) => (
          <li key={feature} className="flex items-start gap-3 text-sm">
            <svg
              className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                highlighted ? "text-emerald-400" : "text-zinc-500"
              }`}
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
            <span className="text-zinc-300">{feature}</span>
          </li>
        ))}
      </ul>

      <a
        href="#"
        className={`block w-full text-center py-3 rounded-xl text-sm font-medium transition-all ${
          highlighted
            ? "bg-emerald-500 hover:bg-emerald-400 text-black hover:shadow-[0_0_30px_rgba(16,185,129,0.3)]"
            : "bg-zinc-800 hover:bg-zinc-700 text-white border border-zinc-700"
        }`}
      >
        {cta}
      </a>
    </motion.div>
  );
}
