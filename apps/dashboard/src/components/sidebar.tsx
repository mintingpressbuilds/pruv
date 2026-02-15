"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  Link2,
  FileCheck,
  ScanSearch,
  Settings,
  Key,
  Users,
  CreditCard,
  LogOut,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useState } from "react";
import { auth } from "@/lib/api";
import { PruvIcon } from "@/components/icons/pruv-icon";

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
  children?: NavItem[];
}

const navItems: NavItem[] = [
  {
    href: "/",
    label: "overview",
    icon: <LayoutDashboard size={20} />,
  },
  {
    href: "/chains",
    label: "chains",
    icon: <Link2 size={20} />,
  },
  {
    href: "/receipts",
    label: "receipts",
    icon: <FileCheck size={20} />,
  },
  {
    href: "/scan",
    label: "scan",
    icon: <ScanSearch size={20} />,
  },
  {
    href: "/settings",
    label: "settings",
    icon: <Settings size={20} />,
    children: [
      {
        href: "/settings/api-keys",
        label: "api keys",
        icon: <Key size={16} />,
      },
      {
        href: "/settings/team",
        label: "team",
        icon: <Users size={16} />,
      },
      {
        href: "/settings/billing",
        label: "billing",
        icon: <CreditCard size={16} />,
      },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(
    pathname.startsWith("/settings")
  );

  const isActive = (href: string): boolean => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 72 : 256 }}
      transition={{ duration: 0.2, ease: "easeInOut" }}
      className="fixed left-0 top-0 bottom-0 z-40 flex flex-col border-r border-[var(--border)] bg-[var(--surface-secondary)]"
    >
      {/* Logo */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-[var(--border)]">
        <Link href="/" className="flex items-center gap-2">
          <PruvIcon size={32} className="text-pruv-600" />
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-lg font-semibold text-[var(--text-primary)]"
            >
              pruv
            </motion.span>
          )}
        </Link>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex h-7 w-7 items-center justify-center rounded-md hover:bg-[var(--surface-tertiary)] text-[var(--text-secondary)] transition-colors"
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-3 space-y-1">
        {navItems.map((item) => (
          <div key={item.href}>
            {item.children ? (
              <>
                <button
                  onClick={() => setSettingsOpen(!settingsOpen)}
                  className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150 ${
                    isActive(item.href)
                      ? "bg-pruv-600/10 text-pruv-400"
                      : "text-[var(--text-secondary)] hover:bg-[var(--surface-tertiary)] hover:text-[var(--text-primary)]"
                  }`}
                >
                  {item.icon}
                  {!collapsed && (
                    <>
                      <span className="flex-1 text-left">{item.label}</span>
                      <motion.div
                        animate={{ rotate: settingsOpen ? 90 : 0 }}
                        transition={{ duration: 0.15 }}
                      >
                        <ChevronRight size={14} />
                      </motion.div>
                    </>
                  )}
                </button>
                {settingsOpen && !collapsed && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.15 }}
                    className="ml-5 mt-1 space-y-0.5 border-l border-[var(--border)] pl-3"
                  >
                    {item.children.map((child) => (
                      <Link
                        key={child.href}
                        href={child.href}
                        className={`flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm transition-all duration-150 ${
                          isActive(child.href)
                            ? "bg-pruv-600/10 text-pruv-400"
                            : "text-[var(--text-secondary)] hover:bg-[var(--surface-tertiary)] hover:text-[var(--text-primary)]"
                        }`}
                      >
                        {child.icon}
                        <span>{child.label}</span>
                      </Link>
                    ))}
                  </motion.div>
                )}
              </>
            ) : (
              <Link
                href={item.href}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150 ${
                  isActive(item.href)
                    ? "bg-pruv-600/10 text-pruv-400"
                    : "text-[var(--text-secondary)] hover:bg-[var(--surface-tertiary)] hover:text-[var(--text-primary)]"
                }`}
              >
                {item.icon}
                {!collapsed && <span>{item.label}</span>}
              </Link>
            )}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-[var(--border)] p-3 space-y-1">
        <a
          href="https://x.com/pruvxy"
          target="_blank"
          rel="noopener noreferrer"
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-[var(--text-secondary)] hover:bg-[var(--surface-tertiary)] hover:text-[var(--text-primary)] transition-all duration-150"
        >
          <svg width={20} height={20} viewBox="0 0 24 24" fill="currentColor">
            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
          </svg>
          {!collapsed && <span>follow on x</span>}
        </a>
        <button
          onClick={() => auth.signOut()}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-[var(--text-secondary)] hover:bg-red-500/10 hover:text-red-400 transition-all duration-150"
        >
          <LogOut size={20} />
          {!collapsed && <span>sign out</span>}
        </button>
      </div>
    </motion.aside>
  );
}
