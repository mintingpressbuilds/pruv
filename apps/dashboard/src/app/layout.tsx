import type { Metadata } from "next";
import { Providers } from "@/components/providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "pruv dashboard",
  description:
    "proof-of-state chain dashboard — verify, track, and audit state transitions",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-[var(--surface)] antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
