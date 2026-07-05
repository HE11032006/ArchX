export default function NavBar({ onBack }) {
  return (
    <nav className="relative z-50 px-8 py-6 flex justify-between items-center"
      style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>

      {/* Logo */}
      <div className="flex items-center gap-4">
        <div className="w-11 h-11 bg-white flex items-center justify-center p-2 flex-shrink-0"
          style={{ boxShadow: '4px 4px 0px var(--neon-cyan)' }}>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#000" strokeWidth="2.5">
            <polyline points="4 17 10 11 4 5" /><line x1="12" y1="19" x2="20" y2="19" />
          </svg>
        </div>
        <div>
          <h2 className="clash-bold tracking-tighter leading-none" style={{ fontSize: '1.75rem' }}>
            ARCH<span style={{ color: '#67e8f9' }}>X</span>
          </h2>
          <p className="label-sm text-muted">Stack Oracle v1.0.4</p>
        </div>
      </div>

      {/* Desktop links */}
      <div className="hidden lg:flex items-center gap-10">
        {onBack ? (
          <button onClick={onBack}
            className="text-xs font-bold uppercase transition-colors hover:text-white"
            style={{ letterSpacing: '0.15em', color: 'rgba(255,255,255,0.6)', background: 'none', border: 'none', cursor: 'pointer' }}>
            ← New Scan
          </button>
        ) : (
          <>
            <a href="#" className="text-xs font-bold uppercase transition-colors hover:text-white"
              style={{ letterSpacing: '0.15em', color: 'rgba(255,255,255,0.6)', textDecoration: 'none' }}>
              Core System
            </a>
            <a href="#" className="text-xs font-bold uppercase transition-colors hover:text-white"
              style={{ letterSpacing: '0.15em', color: 'rgba(255,255,255,0.6)', textDecoration: 'none' }}>
              Datasets
            </a>
            <a href="#" className="text-xs font-bold uppercase transition-colors hover:text-white"
              style={{ letterSpacing: '0.15em', color: 'rgba(255,255,255,0.6)', textDecoration: 'none' }}>
              Licensing
            </a>
          </>
        )}
        <button className="cyber-btn cyber-btn-outline px-7 py-3 text-xs">
          Access Terminal
        </button>
      </div>
    </nav>
  )
}
