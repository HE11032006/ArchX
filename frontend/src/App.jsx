import NavBar from './components/NavBar'
import HeroSection from './components/HeroSection'
import ReportView from './components/ReportView'
import Footer from './components/Footer'
import { mockReport } from './data/mockReport'
import { useState } from 'react'
import './index.css'

export default function App() {
  const [view, setView] = useState('hero') // 'hero' | 'report'
  const [repoUrl, setRepoUrl] = useState('')

  const handleScan = (url) => {
    setRepoUrl(url)
    setView('report')
  }

  return (
    <div className="min-h-screen mesh-gradient relative overflow-hidden flex flex-col">
      {/* Grid overlay */}
      <div className="absolute inset-0 geometric-pattern pointer-events-none" />
      {/* Scanline FX */}
      <div className="scanline" />

      {/* Floating decorative shapes */}
      <div className="floating absolute top-20 left-10 w-32 h-32 border-2 blur-sm"
        style={{ borderColor: 'rgba(0,245,255,0.15)', borderRadius: '50%' }} />
      <div className="floating-delay absolute bottom-20 right-10 w-48 h-48 border-2 blur-sm"
        style={{ borderColor: 'rgba(255,0,255,0.12)', clipPath: 'polygon(50% 0%, 0% 100%, 100% 100%)' }} />
      <div className="absolute top-1/2 left-1/4 w-px h-64 pointer-events-none opacity-30"
        style={{ background: 'linear-gradient(to bottom, transparent, var(--neon-cyan), transparent)' }} />
      <div className="absolute top-1/3 right-1/4 w-px h-64 pointer-events-none opacity-30"
        style={{ background: 'linear-gradient(to bottom, transparent, var(--neon-magenta), transparent)' }} />

      <NavBar onBack={view === 'report' ? () => setView('hero') : null} />

      <main className="flex-1 relative z-10">
        {view === 'hero'
          ? <HeroSection onScan={handleScan} />
          : <ReportView report={mockReport} repoUrl={repoUrl} />
        }
      </main>

      <Footer />
    </div>
  )
}
