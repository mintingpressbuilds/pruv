"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  CreditCard,
  Check,
  ExternalLink,
  Loader2,
  Zap,
} from "lucide-react";
import { toast } from "sonner";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { billing } from "@/lib/api";
import type {
  BillingSubscription,
  BillingUsage,
  BillingPlan,
} from "@/lib/types";

function UsageBar({
  used,
  limit,
  label,
}: {
  used: number;
  limit: number;
  label: string;
}) {
  const pct = limit > 0 ? Math.min((used / limit) * 100, 100) : 0;
  const isHigh = pct > 80;

  return (
    <div>
      <div className="flex items-center justify-between text-xs mb-1.5">
        <span className="text-[var(--text-secondary)]">{label}</span>
        <span className="text-[var(--text-tertiary)]">
          {used.toLocaleString()} / {limit.toLocaleString()}
        </span>
      </div>
      <div className="h-2 rounded-full bg-[var(--surface-tertiary)] overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className={`h-full rounded-full ${
            isHigh
              ? "bg-gradient-to-r from-red-500 to-red-400"
              : "bg-gradient-to-r from-pruv-600 to-pruv-400"
          }`}
        />
      </div>
    </div>
  );
}

export default function BillingPage() {
  const { data: subscription } = useQuery<BillingSubscription>({
    queryKey: ["billing", "subscription"],
    queryFn: () => billing.getSubscription(),
  });

  const { data: usage } = useQuery<BillingUsage>({
    queryKey: ["billing", "usage"],
    queryFn: () => billing.getUsage(),
  });

  const { data: plans = [] } = useQuery<BillingPlan[]>({
    queryKey: ["billing", "plans"],
    queryFn: () => billing.getPlans(),
  });

  const portalMutation = useMutation({
    mutationFn: () => billing.getPortalUrl(),
    onSuccess: (data) => {
      window.location.href = data.url;
    },
  });

  const changePlanMutation = useMutation({
    mutationFn: (planId: string) => billing.changePlan(planId),
    onSuccess: () => {
      toast.success("plan updated");
    },
  });

  const currentPlanId = subscription?.plan.id;

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 ml-64">
        <Header
          title="billing"
          subtitle="manage your plan and usage"
          actions={
            <button
              onClick={() => portalMutation.mutate()}
              disabled={portalMutation.isPending}
              className="flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] px-4 py-2 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            >
              {portalMutation.isPending ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <ExternalLink size={14} />
              )}
              billing portal
            </button>
          }
        />

        <main className="p-6 space-y-6">
          {/* Current usage */}
          {usage && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
                  current usage
                </h3>
                {subscription && (
                  <span
                    className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[10px] font-medium ${
                      subscription.status === "active"
                        ? "border-green-500/20 bg-green-500/10 text-green-400"
                        : "border-yellow-500/20 bg-yellow-500/10 text-yellow-400"
                    }`}
                  >
                    {subscription.status}
                  </span>
                )}
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <UsageBar
                  used={usage.chains_used}
                  limit={usage.chains_limit}
                  label="chains"
                />
                <UsageBar
                  used={usage.receipts_used}
                  limit={usage.receipts_limit}
                  label="receipts"
                />
                <UsageBar
                  used={usage.api_keys_used}
                  limit={usage.api_keys_limit}
                  label="api keys"
                />
                <UsageBar
                  used={usage.team_members_used}
                  limit={usage.team_members_limit}
                  label="team members"
                />
              </div>
            </motion.div>
          )}

          {/* Plans */}
          <div>
            <h3 className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-4">
              plans
            </h3>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {plans.map((plan, i) => {
                const isCurrent = plan.id === currentPlanId;
                return (
                  <motion.div
                    key={plan.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className={`rounded-xl border p-5 ${
                      isCurrent
                        ? "border-pruv-500/30 bg-pruv-500/5"
                        : "border-[var(--border)] bg-[var(--surface-secondary)]"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-semibold text-[var(--text-primary)]">
                        {plan.name}
                      </h4>
                      {isCurrent && (
                        <span className="rounded-full bg-pruv-500/10 border border-pruv-500/20 px-2 py-0.5 text-[10px] text-pruv-400">
                          current
                        </span>
                      )}
                    </div>
                    <div className="mt-2">
                      <span className="text-2xl font-bold text-[var(--text-primary)]">
                        ${plan.price_monthly}
                      </span>
                      {plan.price_monthly > 0 && (
                        <span className="text-xs text-[var(--text-tertiary)]">
                          /mo
                        </span>
                      )}
                    </div>

                    <ul className="mt-4 space-y-2">
                      {plan.features.map((feature) => (
                        <li
                          key={feature}
                          className="flex items-center gap-2 text-xs text-[var(--text-secondary)]"
                        >
                          <Check size={12} className="text-green-400 flex-shrink-0" />
                          {feature}
                        </li>
                      ))}
                    </ul>

                    <div className="mt-4 text-[10px] text-[var(--text-tertiary)] space-y-0.5">
                      <div>{plan.limits.chains.toLocaleString()} chains</div>
                      <div>
                        {plan.limits.entries_per_chain.toLocaleString()} entries/chain
                      </div>
                      <div>{plan.limits.receipts.toLocaleString()} receipts</div>
                      <div>{plan.limits.team_members} team members</div>
                    </div>

                    <button
                      onClick={() => {
                        if (!isCurrent) changePlanMutation.mutate(plan.id);
                      }}
                      disabled={isCurrent || changePlanMutation.isPending}
                      className={`mt-4 w-full rounded-lg px-4 py-2 text-xs font-medium transition-colors ${
                        isCurrent
                          ? "border border-pruv-500/30 text-pruv-400 cursor-default"
                          : plan.tier === "enterprise"
                            ? "bg-[var(--surface-tertiary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                            : "bg-pruv-600 text-white hover:bg-pruv-500"
                      }`}
                    >
                      {isCurrent ? (
                        "current plan"
                      ) : plan.tier === "enterprise" ? (
                        "contact sales"
                      ) : changePlanMutation.isPending ? (
                        <Loader2
                          size={12}
                          className="animate-spin mx-auto"
                        />
                      ) : (
                        <span className="flex items-center justify-center gap-1">
                          <Zap size={10} />
                          upgrade
                        </span>
                      )}
                    </button>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
