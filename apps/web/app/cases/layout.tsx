"use client";

import { ReactNode, useEffect } from "react";
import { useRouter } from "next/navigation";

import { getToken } from "@/lib/session";

export default function CasesLayout({ children }: { children: ReactNode }) {
  const router = useRouter();

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
    }
  }, [router]);

  return <div className="space-y-6">{children}</div>;
}
