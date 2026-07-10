import type { Metadata } from "next";
import { Space_Grotesk } from "next/font/google";

import { AppShell } from "@/shared/components/app-shell";
import { cn } from "@/shared/lib/utils";

import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "ArchX — The Oracle of Stacks",
  description: "Advanced AI-powered architectural analysis tool",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={cn(spaceGrotesk.variable, "font-sans antialiased")}>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
