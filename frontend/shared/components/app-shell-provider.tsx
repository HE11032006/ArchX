"use client";

import { usePathname } from "next/navigation";

import { AppShell } from "@/shared/components/app-shell";

export function AppShellProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const showBack = pathname.startsWith("/report");

  return <AppShell showBack={showBack}>{children}</AppShell>;
}
