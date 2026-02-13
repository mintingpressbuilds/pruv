"use client";

import { motion } from "framer-motion";
import { CodeBlock } from "@/components/code-block";
import { CtaSection } from "@/components/cta-section";

const steps = [
  {
    number: "01",
    title: "Capture X (Before State)",
    description:
      "When a state transition begins, pruv snapshots the current state. This becomes X \u2014 a cryptographically hashed representation of the before state. X can be anything: a database record, a configuration file, an API payload, a file on disk.",
    code: `# X is captured automatically by the decorator
@xy_wrap
def process_order(order: dict) -> dict:
    # At this point, pruv has already captured X = order
    # X is hashed: sha256(canonical(order))
    ...`,
  },
  {
    number: "02",
    title: "Execute Transition",
    description:
      "Your code runs exactly as it normally would. pruv does not modify your business logic, intercept calls, or add middleware. It simply observes the input and the output. Zero performance overhead on your hot path.",
    code: `    # Your code runs unchanged
    validated = validate_payment(order)
    charged = charge_card(validated)
    fulfilled = ship_items(charged)
    return fulfilled`,
  },
  {
    number: "03",
    title: "Capture Y (After State)",
    description:
      "When the function returns, pruv captures the result as Y \u2014 the after state. Y is hashed the same way as X. Now pruv has both endpoints of the transition.",
    code: `    return fulfilled
    # Y is captured: sha256(canonical(fulfilled))
    # pruv now has: X (before), Y (after)`,
  },
  {
    number: "04",
    title: "Generate XY (Proof)",
    description:
      "pruv combines X and Y into a single verifiable record: XY. This record includes the hashes of both states, a timestamp, an optional Ed25519 signature, and a link to the previous entry in the chain. The result is a tamper-evident proof that the transition occurred.",
    code: `# The XY record (simplified)
{
    "id": "xy_8f3a2b1c",
    "x_hash": "sha256:a1b2c3d4...",
    "y_hash": "sha256:e5f6a7b8...",
    "timestamp": "2025-01-15T10:30:00Z",
    "signature": "ed25519:...",
    "prev_entry": "xy_7e2f1a0b",
    "chain_id": "order_processing"
}`,
  },
];

export default function HowItWorksPage() {
  return (
    <div className="pt-24">
      {/* Hero */}
      <section className="section-padding pb-12">
        <div className="container-narrow">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <span className="text-sm text-emerald-400 font-medium">
              How It Works
            </span>
            <h1 className="mt-4 text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight">
              The XY primitive.
            </h1>
            <p className="mt-6 text-xl text-zinc-400 max-w-3xl">
              Every system transforms state. pruv captures the before, the
              after, and generates cryptographic proof that the transition
              occurred. No blockchain. No consensus. Just math.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Core concept */}
      <section className="section-padding pt-8 pb-12">
        <div className="container-narrow">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.6 }}
            className="p-8 sm:p-12 rounded-3xl bg-zinc-900/30 border border-zinc-800"
          >
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold mb-2">The Core Idea</h2>
              <p className="text-zinc-400">
                State transitions are the fundamental unit of change in any
                system.
              </p>
            </div>

            <div className="flex flex-col items-center gap-6">
              <div className="flex flex-wrap items-center justify-center gap-4 text-center">
                <div className="p-4">
                  <div className="font-mono text-2xl font-bold text-zinc-300">
                    f(X) = Y
                  </div>
                  <p className="text-xs text-zinc-500 mt-2">
                    Every function transforms state
                  </p>
                </div>
                <div className="text-zinc-600 text-2xl">&rarr;</div>
                <div className="p-4">
                  <div className="font-mono text-2xl font-bold text-emerald-400">
                    pruv(f)(X) = Y + XY
                  </div>
                  <p className="text-xs text-zinc-500 mt-2">
                    pruv adds proof to every transition
                  </p>
                </div>
              </div>

              <p className="text-sm text-zinc-500 max-w-lg text-center">
                Where XY is a cryptographic record containing hashes of both X
                and Y, a timestamp, an optional signature, and a link to the
                previous record in the chain.
              </p>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Step by step */}
      <section className="section-padding pt-8">
        <div className="container-narrow">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-3xl font-bold mb-16 text-center"
          >
            Step by step
          </motion.h2>

          <div className="space-y-16">
            {steps.map((step, i) => (
              <motion.div
                key={step.number}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.5, delay: 0.1 }}
              >
                <div className="flex items-start gap-6 mb-6">
                  <span className="font-mono text-4xl font-bold text-emerald-500/30 flex-shrink-0">
                    {step.number}
                  </span>
                  <div>
                    <h3 className="text-xl sm:text-2xl font-bold text-white">
                      {step.title}
                    </h3>
                    <p className="mt-3 text-zinc-400 leading-relaxed max-w-2xl">
                      {step.description}
                    </p>
                  </div>
                </div>
                <CodeBlock
                  code={step.code}
                  language="python"
                  showLineNumbers
                />
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Chain Rule */}
      <section className="section-padding">
        <div className="container-narrow">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-3xl font-bold mb-6">The Chain Rule</h2>
            <p className="text-lg text-zinc-400 mb-8 max-w-3xl">
              When the output of one transition becomes the input of the next,
              pruv links them into an unbreakable chain. Each XY record
              references the previous one, creating a directed acyclic graph of
              verified state transitions.
            </p>

            {/* Chain visualization */}
            <div className="p-8 rounded-2xl bg-zinc-900/30 border border-zinc-800 overflow-x-auto">
              <div className="flex items-center gap-3 min-w-max justify-center">
                {["X1", "Y1", "X2", "Y2", "X3", "Y3"].map((label, i) => (
                  <motion.div
                    key={label}
                    initial={{ opacity: 0, scale: 0.8 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.3, delay: i * 0.1 }}
                    className="flex items-center gap-3"
                  >
                    <div
                      className={`w-14 h-14 rounded-xl flex items-center justify-center font-mono font-bold text-lg ${
                        label.startsWith("X")
                          ? "bg-zinc-800 border border-zinc-700 text-zinc-300"
                          : "bg-emerald-500/10 border border-emerald-500/30 text-emerald-400"
                      }`}
                    >
                      {label}
                    </div>
                    {i < 5 && (
                      <svg
                        className={`w-4 h-4 flex-shrink-0 ${
                          i % 2 === 0 ? "text-emerald-500" : "text-zinc-600"
                        }`}
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
                    )}
                  </motion.div>
                ))}
              </div>

              <div className="flex justify-center gap-8 mt-6 text-xs text-zinc-500">
                <div className="flex items-center gap-4">
                  <div className="text-center">
                    <span className="font-mono text-emerald-400">XY1</span>
                    <div className="w-20 h-px bg-zinc-700 mt-1" />
                  </div>
                  <div className="text-center">
                    <span className="font-mono text-emerald-400">XY2</span>
                    <div className="w-20 h-px bg-zinc-700 mt-1" />
                  </div>
                  <div className="text-center">
                    <span className="font-mono text-emerald-400">XY3</span>
                    <div className="w-20 h-px bg-zinc-700 mt-1" />
                  </div>
                </div>
              </div>

              <p className="text-center text-sm text-zinc-500 mt-6">
                Y1 becomes X2. Y2 becomes X3. The chain is cryptographically
                linked.
              </p>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Verification */}
      <section className="section-padding pt-8">
        <div className="container-narrow">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-3xl font-bold mb-6">Verification</h2>
            <p className="text-lg text-zinc-400 mb-8 max-w-3xl">
              Anyone with the XY record can independently verify the proof. No
              special tools, no vendor lock-in, no trust required.
            </p>

            <CodeBlock
              code={`from pruv import verify

# Verify a single entry
result = verify("order_processing", entry_id="xy_8f3a2b1c")
print(result.valid)       # True
print(result.x_hash)      # sha256:a1b2c3d4...
print(result.y_hash)      # sha256:e5f6a7b8...
print(result.chain_valid) # True - all previous entries also valid

# Verify an entire chain
chain = verify("order_processing", full_chain=True)
print(chain.length)       # 1,247 entries
print(chain.valid)        # True - every link verified
print(chain.first_entry)  # xy_00000001
print(chain.last_entry)   # xy_8f3a2b1c`}
              language="python"
              filename="verify.py"
              showLineNumbers
            />
          </motion.div>
        </div>
      </section>

      {/* Properties */}
      <section className="section-padding">
        <div className="container-narrow">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-3xl font-bold mb-12"
          >
            Properties
          </motion.h2>

          <div className="grid sm:grid-cols-2 gap-6">
            {[
              {
                title: "Tamper-evident",
                description:
                  "Any modification to an XY record invalidates the hash chain. Tampering is mathematically detectable.",
              },
              {
                title: "Independently verifiable",
                description:
                  "Anyone can verify a proof using standard cryptographic libraries. No proprietary tools required.",
              },
              {
                title: "Local-first",
                description:
                  "Proofs are generated locally and synced asynchronously. Works offline. Works in air-gapped environments.",
              },
              {
                title: "Redaction-safe",
                description:
                  "Sensitive data can be redacted from the record while preserving the cryptographic proof. The hash still verifies.",
              },
              {
                title: "Append-only",
                description:
                  "Records can only be added, never modified or deleted. The chain is a permanent, ordered log of state transitions.",
              },
              {
                title: "Language-agnostic",
                description:
                  "The XY format is a simple JSON schema. Implement it in any language. Official SDKs for Python, TypeScript, Go, and Rust.",
              },
            ].map((prop, i) => (
              <motion.div
                key={prop.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800"
              >
                <h3 className="text-lg font-semibold text-white mb-2">
                  {prop.title}
                </h3>
                <p className="text-sm text-zinc-400 leading-relaxed">
                  {prop.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <CtaSection />
    </div>
  );
}
