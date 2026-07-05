import { useState } from 'react'

export default function HeroSection({ onScan }) {
  const [url, setUrl] = useState('')
  const [scanning, setScanning] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!url.trim()) return
    setScanning(true)
    // Simulate a 1.5s scan delay before showing report
    setTimeout(() => {
      setScanning(false)
      onScan(url.trim())
    }, 1500)
  }

  return (
    <section className="flex flex-col items-center justify-center px-6 py-16 min-h-[calc(100vh-80px)]">
      <div style={{ maxWidth: '72rem', width: '100%' }}>
        <div className="grid lg:grid-cols-2 gap-20 items-center">

          {/* ── LEFT COLUMN ── */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2.5rem' }}>

            {/* Status badge */}
            <div className="status-badge" style={{ width: 'fit-content' }}>
              <span className="label-sm text-cyan">Status: Analysis Core Active</span>
              <span className="status-dot" />
            </div>

            {/* Main headline */}
            <h1 className="clash-bold tracking-tighter text-white"
              style={{ fontSize: 'clamp(56px, 8vw, 100px)', lineHeight: 0.85 }}>
              THE <span className="text-sharp-gradient">ORACLE</span><br />
              OF YOUR<br />
              <span style={{ color: 'var(--neon-magenta)' }}>STACK.</span>
            </h1>

            {/* Sub-description */}
            <p style={{
              fontSize: '1.1rem', color: 'rgba(255,255,255,0.55)', lineHeight: 1.7,
              maxWidth: '32rem', fontWeight: 300,
              borderLeft: '1px solid rgba(255,255,255,0.2)', paddingLeft: '1.5rem'
            }}>
              Intelligence artificielle avancée pour l'analyse de dette technique, les chemins
              de migration et l'architecture logicielle prédictive — propulsée par Gemma fine-tuné
              sur AMD MI300X.
            </p>

            {/* Input + CTA */}
            <form onSubmit={handleSubmit}>
              <div style={{ position: 'relative', maxWidth: '36rem' }} className="group">
                {/* Glow halo */}
                <div style={{
                  position: 'absolute', inset: '-4px',
                  background: 'linear-gradient(to right, var(--neon-cyan), var(--neon-magenta))',
                  opacity: 0.15, filter: 'blur(8px)', transition: 'opacity 0.4s',
                  pointerEvents: 'none'
                }} />
                <div style={{ position: 'relative', display: 'flex' }}>
                  <div className="cyber-input-wrap" style={{ display: 'flex', alignItems: 'center', padding: '0 1rem' }}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
                      stroke="rgba(255,255,255,0.3)" strokeWidth="2" style={{ flexShrink: 0, marginRight: '0.75rem' }}>
                      <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
                    </svg>
                    <input
                      className="cyber-input"
                      type="text"
                      placeholder="github.com/org/repository"
                      value={url}
                      onChange={e => setUrl(e.target.value)}
                      style={{ padding: '1.1rem 0' }}
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={scanning}
                    className="cyber-btn cyber-btn-primary"
                    style={{
                      padding: '1.1rem 2rem', fontSize: '0.8rem', flexShrink: 0,
                      opacity: scanning ? 0.7 : 1
                    }}>
                    {scanning ? '⟳ Scanning...' : 'Run Scan ▶'}
                  </button>
                </div>
              </div>
            </form>

            {/* Stats strip */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '2rem', paddingTop: '0.5rem' }}>
              {[
                { value: '12.4K', label: 'Repos Analyzed' },
                { value: '98.7%', label: 'Accuracy Score', color: 'var(--neon-cyan)' },
                { value: '4.2s', label: 'Avg Scan Time' },
              ].map((stat, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
                  {i > 0 && <div style={{ width: '1px', height: '40px', background: 'rgba(255,255,255,0.1)' }} />}
                  <div>
                    <div className="clash-bold" style={{ fontSize: '1.5rem', color: stat.color || '#fff' }}>
                      {stat.value}
                    </div>
                    <div className="label-sm text-muted">{stat.label}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* ── RIGHT COLUMN: Live Analysis Preview ── */}
          <div className="hidden lg:block" style={{ position: 'relative' }}>
            <div style={{
              position: 'absolute', inset: 0, borderRadius: '50%',
              background: 'rgba(0,245,255,0.1)', filter: 'blur(100px)'
            }} />
            <div className="neon-card" style={{ padding: '1.5rem', position: 'relative', overflow: 'hidden' }}>
              {/* Card header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', paddingBottom: '1rem', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                <span className="font-mono" style={{ fontSize: '10px', color: 'var(--neon-cyan)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                  Process: Migration Simulation
                </span>
                <div style={{ display: 'flex', gap: '6px' }}>
                  {['rgba(255,255,255,0.15)', 'rgba(255,0,255,0.4)', 'rgba(0,245,255,0.4)'].map((c, i) => (
                    <div key={i} style={{ width: 8, height: 8, borderRadius: '50%', background: c }} />
                  ))}
                </div>
              </div>

              {/* Metrics */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                {/* Bars */}
                {[
                  { label: 'Complexity Coefficient', value: 84.2, color: 'var(--neon-magenta)' },
                  { label: 'Test Coverage', value: 66.6, color: 'var(--neon-cyan)' },
                ].map(bar => (
                  <div key={bar.label} style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}
                      className="font-mono" >
                      <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase' }}>{bar.label}</span>
                      <span style={{ fontSize: '10px', color: bar.color }}>{bar.value}%</span>
                    </div>
                    <div className="progress-track">
                      <div className="progress-fill" style={{ width: `${bar.value}%`, background: bar.color, boxShadow: `0 0 8px ${bar.color}` }} />
                    </div>
                  </div>
                ))}

                {/* KPI Cards */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  {[
                    { label: 'Project Health', value: '7.4', suffix: '/10', color: 'var(--neon-cyan)' },
                    { label: 'Migration ROI', value: '2.4x', color: 'var(--neon-magenta)' },
                  ].map(kpi => (
                    <div key={kpi.label} style={{
                      padding: '1rem', background: 'rgba(255,255,255,0.04)',
                      border: '1px solid rgba(255,255,255,0.08)'
                    }}>
                      <span className="label-sm" style={{ display: 'block', marginBottom: '0.5rem', color: kpi.color }}>
                        {kpi.label}
                      </span>
                      <span className="clash-bold" style={{ fontSize: '1.5rem' }}>
                        {kpi.value}
                        {kpi.suffix && <span style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.35)', marginLeft: '3px' }}>{kpi.suffix}</span>}
                      </span>
                    </div>
                  ))}
                </div>

                {/* Terminal lines */}
                <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '1rem' }}>
                  {[
                    { icon: 'cyan', text: 'Analyzed: 1,402 files across 38 modules' },
                    { icon: 'cyan', text: 'Detected: Python / Django / PostgreSQL' },
                    { icon: 'cyan', text: 'Anti-patterns: 3 identified' },
                    { icon: 'magenta', text: 'Recommend: Refactoring + Microservices...', pulse: true },
                  ].map((line, i) => (
                    <div key={i} className={`terminal-line flex items-center gap-2 ${line.pulse ? 'animate-pulse' : ''}`}>
                      <span style={{ color: line.icon === 'cyan' ? 'var(--neon-cyan)' : 'var(--neon-magenta)' }}>&gt;</span>
                      <span style={{ color: line.pulse ? 'rgba(255,255,255,0.5)' : 'inherit' }}>{line.text}</span>
                      {line.pulse && <span className="cursor-blink" style={{ color: 'var(--neon-magenta)' }}>█</span>}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  )
}
