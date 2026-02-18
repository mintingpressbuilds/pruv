"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { ChevronRight } from "lucide-react";

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
  const breadcrumbs = buildBreadcrumbs(pathname);

  return (
    <header className="sticky top-0 z-30 border-b border-[var(--border)] bg-[var(--surface)] pl-16 pr-6 py-3 lg:px-6">
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1 min-w-0">
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
            <div className="flex items-baseline gap-3">
              <h1 className="text-lg font-semibold text-[var(--text-primary)] leading-tight">
                {title}
              </h1>
              {subtitle && (
                <span className="text-xs text-[var(--text-tertiary)]">
                  {subtitle}
                </span>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 pt-1 flex-shrink-0">
          {actions}
        </div>
      </div>
    </header>
  );
}
