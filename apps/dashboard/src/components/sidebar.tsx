"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  Link2,
  FileCheck,
  ScanSearch,
  Fingerprint,
  FileSearch,
  Settings,
  Key,
  Users,
  CreditCard,
  LogOut,
  LogIn,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
} from "lucide-react";
import { useState, useEffect } from "react";
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
    href: "/identities",
    label: "identities",
    icon: <Fingerprint size={20} />,
  },
  {
    href: "/provenance",
    label: "provenance",
    icon: <FileSearch size={20} />,
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
  const [mobileOpen, setMobileOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(
    pathname.startsWith("/settings")
  );
  const [hasToken, setHasToken] = useState(false);

  // Check auth token on mount
  useEffect(() => {
    setHasToken(!!auth.getToken());
  }, []);

  // Close mobile sidebar on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  const isActive = (href: string): boolean => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  // Mobile sidebar is always full-width
  const showCollapsed = collapsed && !mobileOpen;

  const sidebarContent = (
    <>
      {/* Logo */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-[var(--border)]">
        <Link href="/" className="flex items-center gap-2">
          <PruvIcon size={32} className="text-pruv-400" />
          {!showCollapsed && (
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
        {/* Desktop: collapse toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="hidden lg:flex h-7 w-7 items-center justify-center rounded-md hover:bg-[var(--surface-tertiary)] text-[var(--text-secondary)] transition-colors"
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
        {/* Mobile: close button */}
        <button
          onClick={() => setMobileOpen(false)}
          className="flex lg:hidden h-7 w-7 items-center justify-center rounded-md hover:bg-[var(--surface-tertiary)] text-[var(--text-secondary)] transition-colors"
        >
          <X size={16} />
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
                  {!showCollapsed && (
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
                {settingsOpen && !showCollapsed && (
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
                {!showCollapsed && <span>{item.label}</span>}
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
          {!showCollapsed && <span>follow on x</span>}
        </a>
        {hasToken ? (
          <button
            onClick={() => auth.signOut()}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-[var(--text-secondary)] hover:bg-red-500/10 hover:text-red-400 transition-all duration-150"
          >
            <LogOut size={20} />
            {!showCollapsed && <span>sign out</span>}
          </button>
        ) : (
          <Link
            href="/auth/signin"
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-[var(--text-secondary)] hover:bg-pruv-600/10 hover:text-pruv-400 transition-all duration-150"
          >
            <LogIn size={20} />
            {!showCollapsed && <span>sign in</span>}
          </Link>
        )}
      </div>
    </>
  );

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        onClick={() => setMobileOpen(true)}
        className={`fixed top-3 left-3 z-50 flex lg:hidden h-10 w-10 items-center justify-center rounded-xl bg-[var(--surface-secondary)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all ${
          mobileOpen ? "opacity-0 pointer-events-none" : "opacity-100"
        }`}
        aria-label="Open menu"
      >
        <Menu size={18} />
      </button>

      {/* Mobile backdrop */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={() => setMobileOpen(false)}
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          />
        )}
      </AnimatePresence>

      {/* Sidebar — mobile: slide-in drawer, desktop: fixed */}
      <motion.aside
        initial={false}
        animate={{ width: showCollapsed ? 72 : 256 }}
        transition={{ duration: 0.2, ease: "easeInOut" }}
        className={`fixed left-0 top-0 bottom-0 z-50 flex flex-col border-r border-[var(--border)] bg-[var(--surface-secondary)] transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {sidebarContent}
      </motion.aside>
    </>
  );
}
