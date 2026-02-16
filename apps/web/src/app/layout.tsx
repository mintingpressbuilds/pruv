import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";

export const metadata: Metadata = {
  title: {
    default: "pruv — Prove what your AI agent did.",
    template: "%s | pruv",
  },
  description:
    "Cryptographic receipts for AI agents. Every action, every tool call, every message — verified with math your agent can't fake.",
  keywords: [
    "pruv",
    "AI agent verification",
    "cryptographic proof",
    "agent receipts",
    "LangChain verification",
    "CrewAI verification",
    "SHA-256",
    "Ed25519",
  ],
  authors: [{ name: "pruv" }],
  openGraph: {
    title: "pruv — Prove what your AI agent did.",
    description: "Cryptographic receipts for AI agents. Every action verified with math your agent can't fake.",
    url: "https://pruv.dev",
    siteName: "pruv",
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "pruv — Prove what your AI agent did.",
    description: "Cryptographic receipts for AI agents. Every action verified with math your agent can't fake.",
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
