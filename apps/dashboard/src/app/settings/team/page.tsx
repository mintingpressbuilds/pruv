"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Users,
  UserPlus,
  Loader2,
  Trash2,
  Mail,
  Clock,
  Shield,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { toast } from "sonner";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { team } from "@/lib/api";
import type { TeamMember, TeamInvite, TeamRole } from "@/lib/types";

const roleConfig: Record<
  TeamRole,
  { label: string; color: string }
> = {
  owner: { label: "owner", color: "text-pruv-400 bg-pruv-500/10 border-pruv-500/20" },
  admin: { label: "admin", color: "text-blue-400 bg-blue-500/10 border-blue-500/20" },
  member: { label: "member", color: "text-green-400 bg-green-500/10 border-green-500/20" },
  viewer: { label: "viewer", color: "text-[var(--text-tertiary)] bg-[var(--surface-tertiary)] border-[var(--border)]" },
};

export default function TeamPage() {
  const queryClient = useQueryClient();
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<TeamRole>("member");

  const { data: members = [], isLoading: membersLoading } = useQuery<
    TeamMember[]
  >({
    queryKey: ["team", "members"],
    queryFn: () => team.listMembers(),
  });

  const { data: invites = [] } = useQuery<TeamInvite[]>({
    queryKey: ["team", "invites"],
    queryFn: () => team.listInvites(),
  });

  const inviteMutation = useMutation({
    mutationFn: () => team.inviteMember({ email: inviteEmail, role: inviteRole }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team", "invites"] });
      setInviteEmail("");
      toast.success("invite sent");
    },
  });

  const removeMutation = useMutation({
    mutationFn: (id: string) => team.removeMember(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team", "members"] });
      toast.success("member removed");
    },
  });

  const cancelInviteMutation = useMutation({
    mutationFn: (id: string) => team.cancelInvite(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team", "invites"] });
      toast.success("invite cancelled");
    },
  });

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 ml-64">
        <Header title="team" subtitle="manage team members" />

        <main className="p-6 max-w-3xl space-y-6">
          {/* Invite form */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-5">
            <h3 className="text-sm font-medium text-[var(--text-primary)] mb-1">
              invite team member
            </h3>
            <p className="text-xs text-[var(--text-tertiary)] mb-4">
              team members can view and manage chains based on their role
            </p>
            <div className="flex items-center gap-3">
              <input
                type="email"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="colleague@company.com"
                className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:border-pruv-500/50 focus:outline-none"
              />
              <select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value as TeamRole)}
                className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2.5 text-sm text-[var(--text-secondary)] focus:border-pruv-500/50 focus:outline-none"
              >
                <option value="viewer">viewer</option>
                <option value="member">member</option>
                <option value="admin">admin</option>
              </select>
              <button
                onClick={() => inviteMutation.mutate()}
                disabled={!inviteEmail || inviteMutation.isPending}
                className="flex items-center gap-2 rounded-lg bg-pruv-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-pruv-500 transition-colors disabled:opacity-50"
              >
                {inviteMutation.isPending ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <UserPlus size={14} />
                )}
                invite
              </button>
            </div>
          </div>

          {/* Members list */}
          <div>
            <h3 className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-3">
              team members ({members.length})
            </h3>

            {membersLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div
                    key={i}
                    className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-4 animate-pulse"
                  >
                    <div className="flex items-center gap-3">
                      <div className="h-9 w-9 rounded-full bg-[var(--surface-tertiary)]" />
                      <div>
                        <div className="h-4 w-32 rounded bg-[var(--surface-tertiary)]" />
                        <div className="mt-1 h-3 w-24 rounded bg-[var(--surface-tertiary)]" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-2">
                {members.map((member, i) => {
                  const role = roleConfig[member.role];
                  return (
                    <motion.div
                      key={member.id}
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.03 }}
                      className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] p-4"
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-pruv-500/10 text-pruv-400 text-sm font-semibold">
                          {member.name.charAt(0).toLowerCase()}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-[var(--text-primary)]">
                              {member.name}
                            </span>
                            <span
                              className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-medium ${role.color}`}
                            >
                              <Shield size={8} />
                              {role.label}
                            </span>
                          </div>
                          <span className="text-xs text-[var(--text-tertiary)]">
                            {member.email}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-[var(--text-tertiary)]">
                          joined{" "}
                          {formatDistanceToNow(new Date(member.joined_at), {
                            addSuffix: true,
                          })}
                        </span>
                        {member.role !== "owner" && (
                          <button
                            onClick={() => removeMutation.mutate(member.id)}
                            className="flex items-center gap-1 rounded-lg border border-[var(--border)] px-2.5 py-1.5 text-xs text-[var(--text-tertiary)] hover:text-red-400 hover:border-red-500/30 transition-colors"
                          >
                            <Trash2 size={10} />
                            remove
                          </button>
                        )}
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Pending invites */}
          {invites.length > 0 && (
            <div>
              <h3 className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-3">
                pending invites ({invites.length})
              </h3>
              <div className="space-y-2">
                {invites.map((invite) => (
                  <div
                    key={invite.id}
                    className="flex items-center justify-between rounded-xl border border-dashed border-[var(--border)] bg-[var(--surface-secondary)] p-4"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--surface-tertiary)] text-[var(--text-tertiary)]">
                        <Mail size={14} />
                      </div>
                      <div>
                        <span className="text-sm text-[var(--text-primary)]">
                          {invite.email}
                        </span>
                        <div className="flex items-center gap-2 text-xs text-[var(--text-tertiary)]">
                          <span>{invite.role}</span>
                          <Clock size={10} />
                          <span>
                            expires{" "}
                            {formatDistanceToNow(new Date(invite.expires_at), {
                              addSuffix: true,
                            })}
                          </span>
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => cancelInviteMutation.mutate(invite.id)}
                      className="text-xs text-[var(--text-tertiary)] hover:text-red-400 transition-colors"
                    >
                      cancel
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
