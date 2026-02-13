import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";

export const metadata: Metadata = {
  title: {
    default: "pruv — Prove what happened.",
    template: "%s | pruv",
  },
  description:
    "Cryptographic verification for any system. Prove what happened with immutable, verifiable records.",
  keywords: [
    "pruv",
    "verification",
    "cryptographic proof",
    "audit trail",
    "observability",
    "compliance",
  ],
  authors: [{ name: "pruv" }],
  openGraph: {
    title: "pruv — Prove what happened.",
    description: "Cryptographic verification for any system.",
    url: "https://pruv.dev",
    siteName: "pruv",
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "pruv — Prove what happened.",
    description: "Cryptographic verification for any system.",
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
    <html lang="en" className="dark">
      <body className="min-h-screen flex flex-col">
        <Navbar />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
