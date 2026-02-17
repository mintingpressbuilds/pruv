"use client";

import { useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { auth } from "@/lib/api";

export default function AuthCallbackPage() {
  const searchParams = useSearchParams();
  const router = useRouter();

  useEffect(() => {
    const token = searchParams.get("token");
    if (token) {
      auth.setToken(token);
      router.replace("/");
    } else {
      router.replace("/auth/signin");
    }
  }, [searchParams, router]);

  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", color: "#999", fontFamily: "var(--font-mono, monospace)" }}>
      signing in...
    </div>
  );
}
