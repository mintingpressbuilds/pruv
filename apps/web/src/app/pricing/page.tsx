"use client";

import { motion } from "framer-motion";
import { PricingCard } from "@/components/pricing-card";
import { CtaSection } from "@/components/cta-section";

const tiers = [
  {
    name: "Free",
    price: "$0",
    period: "",
    description: "For personal projects and experimentation.",
    features: [
      "1,000 entries per month",
      "Core XY verification",
      "SHA-256 hash chains",
      "Python SDK",
      "Community support",
      "7-day data retention",
    ],
    highlighted: false,
    cta: "Start Free",
  },
  {
    name: "Pro",
    price: "$29",
    period: "/mo",
    description: "For professionals and growing projects.",
    features: [
      "50,000 entries per month",
      "Everything in Free",
      "Checkpoints & snapshots",
      "Ed25519 signatures",
      "PDF export & reports",
      "Webhook notifications",
      "90-day data retention",
      "Email support",
    ],
    highlighted: true,
    cta: "Start Pro Trial",
  },
  {
    name: "Team",
    price: "$99",
    period: "/mo",
    description: "For teams that need compliance and scale.",
    features: [
      "500,000 entries per month",
      "Everything in Pro",
      "SSO / SAML integration",
      "Webhook integrations",
      "Custom redaction rules",
      "99.9% uptime SLA",
      "1-year data retention",
      "Priority support",
    ],
    highlighted: false,
    cta: "Start Team Trial",
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    description: "For organizations with complex requirements.",
    features: [
      "Unlimited entries",
      "Everything in Team",
      "On-premise deployment",
      "Air-gapped environments",
      "Custom integrations",
      "Dedicated support engineer",
      "Custom data retention",
      "SOC 2 / HIPAA compliance",
      "Custom SLA",
    ],
    highlighted: false,
    cta: "Contact Sales",
  },
];

export default function PricingPage() {
  return (
    <div className="pt-24">
      <section className="section-padding">
        <div className="container-wide">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center mb-16"
          >
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight">
              Simple, transparent pricing.
            </h1>
            <p className="mt-6 text-xl text-zinc-400 max-w-2xl mx-auto">
              Start free. Scale as you grow. No surprises.
            </p>
          </motion.div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {tiers.map((tier, i) => (
              <PricingCard key={tier.name} {...tier} index={i} />
            ))}
          </div>

          {/* FAQ */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.5 }}
            className="mt-24 max-w-3xl mx-auto"
          >
            <h2 className="text-2xl font-bold text-center mb-12">
              Frequently asked questions
            </h2>

            <div className="space-y-6">
              {[
                {
                  q: "What counts as an entry?",
                  a: "An entry is a single X \u2192 Y state transition record. Each time you call xy_wrap or create a proof, that counts as one entry. Verification lookups are free and unlimited.",
                },
                {
                  q: "Can I switch plans anytime?",
                  a: "Yes. Upgrade or downgrade at any time. When upgrading, you get immediate access to new features. When downgrading, the change takes effect at the end of your billing cycle.",
                },
                {
                  q: "What happens when I exceed my monthly limit?",
                  a: "We will notify you at 80% and 100% usage. Once you hit your limit, new entries are queued and processed when your limit resets. No data is ever lost.",
                },
                {
                  q: "Is there a self-hosted option?",
                  a: "Yes. Enterprise customers can deploy pruv on-premise or in air-gapped environments. Contact sales for details.",
                },
                {
                  q: "Do you offer annual billing?",
                  a: "Yes. Annual plans come with a 20% discount. Contact us to switch to annual billing.",
                },
              ].map((faq) => (
                <div
                  key={faq.q}
                  className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800"
                >
                  <h3 className="font-semibold text-white mb-2">{faq.q}</h3>
                  <p className="text-sm text-zinc-400 leading-relaxed">
                    {faq.a}
                  </p>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      <CtaSection
        title="Ready to start proving?"
        subtitle="Get started with the free tier. No credit card required."
      />
    </div>
  );
}
