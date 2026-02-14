"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const links = [
  { href: "/how-it-works", label: "how it works" },
  { href: "/pricing", label: "pricing" },
  { href: "/industries", label: "industries" },
  { href: "/security", label: "security" },
  { href: "https://docs.pruv.dev", label: "docs", external: true },
];

export function Navbar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      <nav className="navbar">
        <div className="container">
          <Link href="/" className="navbar-logo">
            pruv<span className="logo-accent">.</span>
          </Link>
          <div className="navbar-links">
            {links.map((link) =>
              link.external ? (
                <a key={link.href} href={link.href}>
                  {link.label}
                </a>
              ) : (
                <Link
                  key={link.href}
                  href={link.href}
                  className={pathname === link.href ? "active" : ""}
                >
                  {link.label}
                </Link>
              )
            )}
          </div>
          <button
            className="navbar-mobile-toggle"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
          >
            {mobileOpen ? "\u2715" : "\u2261"}
          </button>
        </div>
      </nav>
      <div className={`navbar-mobile-menu${mobileOpen ? " open" : ""}`}>
        {links.map((link) =>
          link.external ? (
            <a key={link.href} href={link.href} onClick={() => setMobileOpen(false)}>
              {link.label}
            </a>
          ) : (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setMobileOpen(false)}
            >
              {link.label}
            </Link>
          )
        )}
      </div>
    </>
  );
}
