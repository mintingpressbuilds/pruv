"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { ChevronRight, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { motion } from "framer-motion";

interface Breadcrumb {
  label: string;
  href: string;
}

function buildBreadcrumbs(pathname: string): Breadcrumb[] {
  const segments = pathname.split("/").filter(Boolean);
  const crumbs: Breadcrumb[] = [{ label: "pruv", href: "/" }];

  let currentPath = "";
  for (const segment of segments) {
    currentPath += `/${segment}`;
    // Skip dynamic segments that look like IDs
    const label = segment.startsWith("[")
      ? segment.replace(/\[|\]/g, "")
      : segment;
    crumbs.push({ label, href: currentPath });
  }

  return crumbs;
}

interface HeaderProps {
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export function Header({ title, subtitle, actions }: HeaderProps) {
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();
  const breadcrumbs = buildBreadcrumbs(pathname);

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-[var(--border)] bg-[var(--surface)]/80 px-6 backdrop-blur-xl">
      <div className="flex flex-col justify-center">
        {/* Breadcrumbs */}
        <nav className="flex items-center gap-1 text-xs text-[var(--text-tertiary)]">
          {breadcrumbs.map((crumb, i) => (
            <span key={crumb.href} className="flex items-center gap-1">
              {i > 0 && <ChevronRight size={12} />}
              {i < breadcrumbs.length - 1 ? (
                <Link
                  href={crumb.href}
                  className="hover:text-[var(--text-secondary)] transition-colors"
                >
                  {crumb.label}
                </Link>
              ) : (
                <span className="text-[var(--text-secondary)]">
                  {crumb.label}
                </span>
              )}
            </span>
          ))}
        </nav>

        {/* Title */}
        {title && (
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-semibold text-[var(--text-primary)]">
              {title}
            </h1>
            {subtitle && (
              <span className="text-sm text-[var(--text-tertiary)]">
                {subtitle}
              </span>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        {actions}

        {/* Theme toggle */}
        <motion.button
          whileTap={{ scale: 0.9 }}
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
          aria-label="Toggle theme"
        >
          {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
        </motion.button>
      </div>
    </header>
  );
}
