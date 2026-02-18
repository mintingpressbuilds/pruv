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
  { href: "https://github.com/mintingpressbuilds/pruv", label: "github", external: true },
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
                <a key={link.href} href={link.href} target="_blank" rel="noopener noreferrer">
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
            <a href="https://app.pruv.dev" className="navbar-signin">Sign in</a>
            <a href="https://app.pruv.dev/scan" className="navbar-cta">Get started &rarr;</a>
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
      {mobileOpen && (
        <div
          className="navbar-mobile-backdrop"
          onClick={() => setMobileOpen(false)}
        />
      )}
      <div className={`navbar-mobile-menu${mobileOpen ? " open" : ""}`}>
        {links.map((link) =>
          link.external ? (
            <a key={link.href} href={link.href} target="_blank" rel="noopener noreferrer" onClick={() => setMobileOpen(false)}>
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
        <a href="https://app.pruv.dev" onClick={() => setMobileOpen(false)}>Sign in</a>
        <a href="https://app.pruv.dev/scan" className="navbar-mobile-cta" onClick={() => setMobileOpen(false)}>Get started &rarr;</a>
      </div>
    </>
  );
}
