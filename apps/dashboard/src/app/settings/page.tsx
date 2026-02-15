"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Key, Users, CreditCard, ArrowRight } from "lucide-react";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";

const settingsSections = [
  {
    title: "api keys",
    description: "manage your pv_live_ and pv_test_ api keys",
    href: "/settings/api-keys",
    icon: <Key size={20} className="text-pruv-400" />,
    color: "bg-pruv-500/10",
  },
  {
    title: "team",
    description: "invite members, manage roles and permissions",
    href: "/settings/team",
    icon: <Users size={20} className="text-blue-400" />,
    color: "bg-blue-500/10",
  },
  {
    title: "billing",
    description: "manage your subscription and view usage",
    href: "/settings/billing",
    icon: <CreditCard size={20} className="text-green-400" />,
    color: "bg-green-500/10",
  },
];

export default function SettingsPage() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 ml-0 lg:ml-64">
        <Header title="settings" />

        <main className="p-6 max-w-2xl space-y-3">
          {settingsSections.map((section, i) => (
            <motion.div
              key={section.href}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <Link
                href={section.href}
                className="group flex items-center gap-4 rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5 hover:border-pruv-500/30 transition-all duration-200"
              >
                <div
                  className={`flex h-11 w-11 items-center justify-center rounded-xl ${section.color}`}
                >
                  {section.icon}
                </div>
                <div className="flex-1">
                  <h3 className="text-sm font-medium text-[var(--text-primary)] group-hover:text-pruv-400 transition-colors">
                    {section.title}
                  </h3>
                  <p className="mt-0.5 text-xs text-[var(--text-tertiary)]">
                    {section.description}
                  </p>
                </div>
                <ArrowRight
                  size={16}
                  className="text-[var(--text-tertiary)] group-hover:text-pruv-400 transition-colors"
                />
              </Link>
            </motion.div>
          ))}
        </main>
      </div>
    </div>
  );
}
