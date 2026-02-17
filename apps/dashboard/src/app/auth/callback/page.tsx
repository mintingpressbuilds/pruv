"use client";

import { Suspense, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { auth } from "@/lib/api";

function CallbackHandler() {
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

  return null;
}

export default function AuthCallbackPage() {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", color: "#999", fontFamily: "var(--font-mono, monospace)" }}>
      <Suspense fallback="signing in...">
        <CallbackHandler />
      </Suspense>
      signing in...
    </div>
  );
}
