"use client";

import { motion } from "framer-motion";
import Link from "next/link";

const posts = [
  {
    title: "Introducing pruv: Cryptographic Verification for Any System",
    description:
      "We built pruv because the world runs on state transitions, but nobody can prove they happened. Today, we are changing that with the XY primitive.",
    date: "2025-01-15",
    category: "Announcement",
    readTime: "5 min read",
  },
  {
    title: "Why Logs Are Not Proof",
    description:
      "Logs tell you what someone said happened. But logs can be modified, deleted, or fabricated. Here is why cryptographic verification is the next step beyond observability.",
    date: "2025-01-12",
    category: "Engineering",
    readTime: "8 min read",
  },
  {
    title: "The XY Primitive: A New Foundation for Trust",
    description:
      "Every system transforms state. We introduce the XY primitive: a simple, composable unit of cryptographic proof for any state transition.",
    date: "2025-01-10",
    category: "Technical",
    readTime: "12 min read",
  },
  {
    title: "How pruv Handles Redaction Without Breaking Proofs",
    description:
      "Sensitive data needs to be removed from audit trails. But redaction usually breaks verification. Here is how pruv solves this with hash commitments.",
    date: "2025-01-08",
    category: "Technical",
    readTime: "10 min read",
  },
  {
    title: "pruv for AI Agents: Accountability at Machine Speed",
    description:
      "Autonomous agents make decisions without human oversight. We explore how pruv brings cryptographic accountability to AI systems without slowing them down.",
    date: "2025-01-05",
    category: "Use Cases",
    readTime: "7 min read",
  },
];

export default function BlogPage() {
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
              Blog
            </h1>
            <p className="mt-6 text-xl text-zinc-400">
              Engineering insights, product updates, and the philosophy behind
              cryptographic verification.
            </p>
          </motion.div>

          <div className="space-y-6">
            {posts.map((post, i) => (
              <motion.article
                key={post.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-30px" }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
              >
                <Link
                  href="#"
                  className="block group p-6 sm:p-8 rounded-2xl bg-zinc-900/50 border border-zinc-800 hover:border-emerald-500/20 transition-all"
                >
                  <div className="flex flex-wrap items-center gap-3 mb-4">
                    <span className="px-2.5 py-0.5 text-xs font-medium bg-emerald-500/10 text-emerald-400 rounded-full border border-emerald-500/20">
                      {post.category}
                    </span>
                    <span className="text-xs text-zinc-500">{post.date}</span>
                    <span className="text-xs text-zinc-600">&middot;</span>
                    <span className="text-xs text-zinc-500">
                      {post.readTime}
                    </span>
                  </div>
                  <h2 className="text-xl sm:text-2xl font-bold text-white group-hover:text-emerald-400 transition-colors mb-3">
                    {post.title}
                  </h2>
                  <p className="text-zinc-400 leading-relaxed">
                    {post.description}
                  </p>
                  <div className="mt-4 flex items-center gap-1 text-sm text-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity">
                    Read more
                    <svg
                      className="w-4 h-4"
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
                  </div>
                </Link>
              </motion.article>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
