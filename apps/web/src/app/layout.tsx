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
    "Cryptographic verification primitive. Capture the before, the after, create proof. Chain rule: Entry[N].x == Entry[N-1].y.",
  keywords: [
    "pruv",
    "verification",
    "cryptographic proof",
    "XY chain",
    "state transformation",
    "Ed25519",
    "SHA-256",
  ],
  authors: [{ name: "pruv" }],
  openGraph: {
    title: "pruv — Prove what happened.",
    description: "Cryptographic verification primitive for any system that transforms state.",
    url: "https://pruv.dev",
    siteName: "pruv",
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "pruv — Prove what happened.",
    description: "Cryptographic verification primitive for any system that transforms state.",
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
