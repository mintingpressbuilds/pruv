"use client";

import { motion } from "framer-motion";

interface Row {
  feature: string;
  logs: string;
  traces: string;
  pruv: string;
}

const rows: Row[] = [
  {
    feature: "What it records",
    logs: "Text messages",
    traces: "Request spans",
    pruv: "State transitions (X \u2192 Y)",
  },
  {
    feature: "Tamper-evident",
    logs: "No",
    traces: "No",
    pruv: "Yes \u2014 cryptographic hash chain",
  },
  {
    feature: "Verifiable",
    logs: "No",
    traces: "No",
    pruv: "Yes \u2014 anyone can verify",
  },
  {
    feature: "Structured by default",
    logs: "Rarely",
    traces: "Partially",
    pruv: "Always \u2014 typed before/after",
  },
  {
    feature: "Chain of custody",
    logs: "No",
    traces: "No",
    pruv: "Yes \u2014 chain rule links entries",
  },
  {
    feature: "Offline support",
    logs: "Limited",
    traces: "No",
    pruv: "Yes \u2014 local-first, sync later",
  },
  {
    feature: "Redaction support",
    logs: "Manual",
    traces: "Manual",
    pruv: "Auto-redaction with proof intact",
  },
  {
    feature: "Compliance-ready",
    logs: "Requires tooling",
    traces: "Requires tooling",
    pruv: "Built-in \u2014 SOC 2, HIPAA, GDPR",
  },
];

export function ComparisonTable() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.6 }}
      className="overflow-x-auto"
    >
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-zinc-800">
            <th className="text-left py-4 px-4 text-zinc-500 font-medium w-1/4">
              Feature
            </th>
            <th className="text-left py-4 px-4 text-zinc-500 font-medium w-1/4">
              Logs
            </th>
            <th className="text-left py-4 px-4 text-zinc-500 font-medium w-1/4">
              Traces
            </th>
            <th className="text-left py-4 px-4 font-medium w-1/4">
              <span className="gradient-text font-semibold">pruv</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <motion.tr
              key={row.feature}
              initial={{ opacity: 0, x: -10 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.3, delay: i * 0.05 }}
              className="border-b border-zinc-800/50 hover:bg-zinc-900/30"
            >
              <td className="py-4 px-4 text-zinc-300 font-medium">
                {row.feature}
              </td>
              <td className="py-4 px-4 text-zinc-500">{row.logs}</td>
              <td className="py-4 px-4 text-zinc-500">{row.traces}</td>
              <td className="py-4 px-4 text-emerald-400">{row.pruv}</td>
            </motion.tr>
          ))}
        </tbody>
      </table>
    </motion.div>
  );
}
