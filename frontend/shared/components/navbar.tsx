"use client";

import Link from "next/link";

interface NavbarProps {
  showBack?: boolean;
}

export function Navbar({ showBack = false }: NavbarProps) {
  return (
    <nav className="relative z-50 flex items-center justify-between border-b border-white/6 px-8 py-6">
      <div className="flex items-center gap-4">
        <div
          className="flex h-11 w-11 flex-shrink-0 items-center justify-center bg-white p-2"
          style={{ boxShadow: "4px 4px 0px var(--neon-cyan)" }}
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#000" strokeWidth="2.5">
            <polyline points="4 17 10 11 4 5" />
            <line x1="12" y1="19" x2="20" y2="19" />
          </svg>
        </div>
        <div>
          <Link href="/" className="clash-bold text-[1.75rem] leading-none tracking-tighter text-white no-underline">
            ARCH<span style={{ color: "#67e8f9" }}>X</span>
          </Link>
          <p className="label-sm text-muted">Stack Oracle v1.0.4</p>
        </div>
      </div>

      <div className="hidden items-center gap-10 lg:flex">
        {showBack ? (
          <Link
            href="/"
            className="text-xs font-bold uppercase tracking-[0.15em] text-white/60 no-underline transition-colors hover:text-white"
          >
            ← New Scan
          </Link>
        ) : (
          <>
            <span className="text-xs font-bold uppercase tracking-[0.15em] text-white/60">Core System</span>
            <span className="text-xs font-bold uppercase tracking-[0.15em] text-white/60">Datasets</span>
            <span className="text-xs font-bold uppercase tracking-[0.15em] text-white/60">Licensing</span>
          </>
        )}
        <button type="button" className="cyber-btn cyber-btn-outline px-7 py-3 text-xs">
          Access Terminal
        </button>
      </div>
    </nav>
  );
}
