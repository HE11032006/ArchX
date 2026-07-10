import type { Metadata } from "next";
import { Space_Grotesk } from "next/font/google";

import { AppShellProvider } from "@/shared/components/app-shell-provider";
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
        <AppShellProvider>{children}</AppShellProvider>
      </body>
    </html>
  );
}
