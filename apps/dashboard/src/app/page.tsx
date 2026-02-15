"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  Link2,
  FileCheck,
  Activity,
  TrendingUp,
  ArrowRight,
  AlertTriangle,
  Plus,
  ScanSearch,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { dashboard } from "@/lib/api";
import type { DashboardStats, ActivityItem } from "@/lib/types";

const activityTypeConfig: Record<
  ActivityItem["type"],
  { icon: React.ReactNode; color: string }
> = {
  chain_created: {
    icon: <Link2 size={14} />,
    color: "text-pruv-400 bg-pruv-500/10",
  },
  entry_added: {
    icon: <Plus size={14} />,
    color: "text-blue-400 bg-blue-500/10",
  },
  receipt_issued: {
    icon: <FileCheck size={14} />,
    color: "text-green-400 bg-green-500/10",
  },
  scan_completed: {
    icon: <ScanSearch size={14} />,
    color: "text-yellow-400 bg-yellow-500/10",
  },
  chain_broken: {
    icon: <AlertTriangle size={14} />,
    color: "text-red-400 bg-red-500/10",
  },
};

function StatCard({
  label,
  value,
  icon,
  color,
  delay,
}: {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  delay: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.3 }}
      className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5 hover:border-pruv-500/30 transition-colors"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[11px] font-medium text-[var(--text-tertiary)] uppercase tracking-widest font-mono">
            {label}
          </p>
          <p className="mt-2 text-2xl font-bold text-[var(--text-primary)] font-mono tabular-nums">
            {value}
          </p>
        </div>
        <div
          className={`flex h-10 w-10 items-center justify-center rounded-lg ${color}`}
        >
          {icon}
        </div>
      </div>
    </motion.div>
  );
}

export default function OverviewPage() {
  const { data: stats, isLoading } = useQuery<DashboardStats>({
    queryKey: ["dashboard", "stats"],
    queryFn: () => dashboard.getStats(),
  });

  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <div className="flex-1 ml-0 lg:ml-64">
        <Header title="overview" subtitle="your pruv dashboard" />

        <main className="p-6 space-y-6 max-w-[1400px]">
          {/* Stats grid */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="total chains"
              value={isLoading ? "—" : (stats?.total_chains ?? 0)}
              icon={<Link2 size={20} className="text-pruv-400" />}
              color="bg-pruv-500/10"
              delay={0}
            />
            <StatCard
              label="total entries"
              value={isLoading ? "—" : (stats?.total_entries ?? 0)}
              icon={<Activity size={20} className="text-blue-400" />}
              color="bg-blue-500/10"
              delay={0.05}
            />
            <StatCard
              label="receipts issued"
              value={isLoading ? "—" : (stats?.total_receipts ?? 0)}
              icon={<FileCheck size={20} className="text-green-400" />}
              color="bg-green-500/10"
              delay={0.1}
            />
            <StatCard
              label="verified"
              value={
                isLoading ? "—" : `${stats?.verified_percentage ?? 0}%`
              }
              icon={<TrendingUp size={20} className="text-pruv-400" />}
              color="bg-pruv-500/10"
              delay={0.15}
            />
          </div>

          {/* Two-column layout */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            {/* Recent activity */}
            <div className="lg:col-span-2 rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-[11px] font-medium text-[var(--text-tertiary)] uppercase tracking-widest font-mono">
                  recent activity
                </h2>
                <Link
                  href="/chains"
                  className="flex items-center gap-1 text-xs text-pruv-400 hover:text-pruv-300 transition-colors"
                >
                  view all <ArrowRight size={12} />
                </Link>
              </div>

              {isLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <div
                      key={i}
                      className="flex items-center gap-3 rounded-lg bg-[var(--surface)] p-3 animate-pulse"
                    >
                      <div className="h-8 w-8 rounded-lg bg-[var(--surface-tertiary)]" />
                      <div className="flex-1">
                        <div className="h-3 w-48 rounded bg-[var(--surface-tertiary)]" />
                        <div className="mt-1.5 h-2 w-24 rounded bg-[var(--surface-tertiary)]" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : stats?.recent_activity && stats.recent_activity.length > 0 ? (
                <div className="space-y-2">
                  {stats.recent_activity.map((activity, i) => {
                    const config = activityTypeConfig[activity.type];
                    return (
                      <motion.div
                        key={activity.id}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.04 }}
                        className="flex items-center gap-3 rounded-lg bg-[var(--surface)] p-3 border border-[var(--border)] hover:border-pruv-500/20 transition-colors"
                      >
                        <div
                          className={`flex h-8 w-8 items-center justify-center rounded-lg ${config.color}`}
                        >
                          {config.icon}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-[var(--text-primary)] truncate">
                            {activity.description}
                          </p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className="text-xs text-[var(--text-tertiary)]">
                              {activity.actor}
                            </span>
                            {activity.chain_name && (
                              <Link
                                href={`/chains/${activity.chain_id}`}
                                className="text-xs text-pruv-400 hover:text-pruv-300"
                              >
                                {activity.chain_name}
                              </Link>
                            )}
                          </div>
                        </div>
                        <span className="text-[10px] text-[var(--text-tertiary)] flex-shrink-0">
                          {formatDistanceToNow(new Date(activity.timestamp), {
                            addSuffix: true,
                          })}
                        </span>
                      </motion.div>
                    );
                  })}
                </div>
              ) : (
                <div className="flex flex-col items-center py-10 text-center">
                  <Activity
                    size={32}
                    className="text-[var(--text-tertiary)] mb-3"
                  />
                  <p className="text-sm text-[var(--text-secondary)]">
                    no recent activity
                  </p>
                  <p className="text-xs text-[var(--text-tertiary)] mt-1">
                    create a chain to get started
                  </p>
                </div>
              )}
            </div>

            {/* Quick actions */}
            <div className="space-y-4">
              <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5">
                <h2 className="text-[11px] font-medium text-[var(--text-tertiary)] uppercase tracking-widest font-mono mb-4">
                  quick actions
                </h2>
                <div className="space-y-2">
                  <Link
                    href="/chains"
                    className="flex items-center gap-3 rounded-lg bg-[var(--surface)] p-3 border border-[var(--border)] hover:border-pruv-500/30 transition-colors group"
                  >
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-pruv-500/10 text-pruv-400 group-hover:bg-pruv-500/20 transition-colors">
                      <Plus size={16} />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-[var(--text-primary)]">
                        new chain
                      </p>
                      <p className="text-xs text-[var(--text-tertiary)]">
                        create a proof-of-state chain
                      </p>
                    </div>
                  </Link>

                  <Link
                    href="/scan"
                    className="flex items-center gap-3 rounded-lg bg-[var(--surface)] p-3 border border-[var(--border)] hover:border-pruv-500/30 transition-colors group"
                  >
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-500/10 text-blue-400 group-hover:bg-blue-500/20 transition-colors">
                      <ScanSearch size={16} />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-[var(--text-primary)]">
                        run scan
                      </p>
                      <p className="text-xs text-[var(--text-tertiary)]">
                        verify an existing chain
                      </p>
                    </div>
                  </Link>

                  <Link
                    href="/settings/api-keys"
                    className="flex items-center gap-3 rounded-lg bg-[var(--surface)] p-3 border border-[var(--border)] hover:border-pruv-500/30 transition-colors group"
                  >
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-green-500/10 text-green-400 group-hover:bg-green-500/20 transition-colors">
                      <Activity size={16} />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-[var(--text-primary)]">
                        api keys
                      </p>
                      <p className="text-xs text-[var(--text-tertiary)]">
                        manage pv_live_ and pv_test_ keys
                      </p>
                    </div>
                  </Link>
                </div>
              </div>

              {/* Chain rule reminder */}
              <div className="rounded-xl border border-pruv-500/20 bg-pruv-500/5 p-5">
                <h3 className="text-[11px] font-medium text-pruv-400 uppercase tracking-widest font-mono mb-3">
                  chain rule
                </h3>
                <p className="text-sm text-pruv-400 font-mono font-semibold">
                  entry[n].x == entry[n-1].y
                </p>
                <p className="mt-2 text-xs text-[var(--text-tertiary)] leading-relaxed">
                  every entry&apos;s input state must match the previous
                  entry&apos;s output state. this is the foundation of
                  proof-of-state verification.
                </p>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
