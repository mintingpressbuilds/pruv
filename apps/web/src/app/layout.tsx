import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";

export const metadata: Metadata = {
  title: {
    default: "pruv — Operational proof for any system.",
    template: "%s | pruv",
  },
  description:
    "Cryptographic proof chains for any system. Every action hashed, linked, and verified. Tamper with one entry and the chain breaks.",
  keywords: [
    "pruv",
    "cryptographic proof",
    "verification chain",
    "audit trail",
    "tamper-evident",
    "SHA-256",
    "Ed25519",
    "operational proof",
  ],
  authors: [{ name: "pruv" }],
  openGraph: {
    title: "pruv — Operational proof for any system.",
    description: "Cryptographic proof chains for any system. Every action hashed, linked, and verified.",
    url: "https://pruv.dev",
    siteName: "pruv",
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "pruv — Operational proof for any system.",
    description: "Cryptographic proof chains for any system. Every action hashed, linked, and verified.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        <main>{children}</main>
        <Footer />
      </body>
    </html>
  );
}
