import React, { useEffect, useState } from 'react'
import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import Landing from './pages/Landing.jsx'
import Dashboard from './pages/Dashboard.jsx'
import CaseDetail from './pages/CaseDetail.jsx'
import NonLiquetQueue from './pages/NonLiquetQueue.jsx'
import NewDispute from './pages/NewDispute.jsx'
import SellerRisk from './pages/SellerRisk.jsx'
import PolicyBrowser from './pages/PolicyBrowser.jsx'
import Analytics from './pages/Analytics.jsx'
import Timeline from './pages/Timeline.jsx'
import Automation from './pages/Automation.jsx'

/* ── Icons ─────────────────────────────────────────────────────────────────── */
const Icon = {
  dashboard: (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="currentColor">
      <rect x="1" y="1" width="5.5" height="5.5" rx="1.4" opacity="0.55"/>
      <rect x="8.5" y="1" width="5.5" height="5.5" rx="1.4"/>
      <rect x="1" y="8.5" width="5.5" height="5.5" rx="1.4"/>
      <rect x="8.5" y="8.5" width="5.5" height="5.5" rx="1.4" opacity="0.55"/>
    </svg>
  ),
  analytics: (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
      <polyline points="1,12 4.5,7 7.5,9 10.5,4.5 14,6.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
      <circle cx="14" cy="6.5" r="0.9" fill="currentColor"/>
    </svg>
  ),
  automation: (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
      <path d="M8.5 1.5L3.5 8.5h5l-2 5L14 7H9l1.5-5.5z" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  queue: (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
      <path d="M2 3.5h11M2 7.5h7.5M2 11.5h9.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
    </svg>
  ),
  risk: (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
      <path d="M7.5 1.5L13 4v4c0 3.5-3 5.5-5.5 6.5C5 13.5 2 11.5 2 8V4L7.5 1.5z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round"/>
    </svg>
  ),
  timeline: (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
      <circle cx="7.5" cy="7.5" r="5.5" stroke="currentColor" strokeWidth="1.3"/>
      <path d="M7.5 4V7.5l2.5 2" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
    </svg>
  ),
  policy: (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
      <rect x="2" y="1" width="11" height="13" rx="1.5" stroke="currentColor" strokeWidth="1.3"/>
      <path d="M5 5h5M5 7.5h5M5 10h3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  ),
  plus: (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
      <path d="M7 2v10M2 7h10" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
    </svg>
  ),
  hamburger: (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <path d="M2 4.5h14M2 9h14M2 13.5h14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  ),
  close: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M3 3l10 10M13 3L3 13" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
    </svg>
  ),
  scale: (
    <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
      <line x1="11" y1="3" x2="11" y2="20" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round"/>
      <line x1="3" y1="7" x2="19" y2="7" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round"/>
      <path d="M3 7v4.5A3.5 3.5 0 0 0 10 11.5V7" stroke="var(--accent)" strokeWidth="1.3" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M12 7v4.5A3.5 3.5 0 0 0 19 11.5V7" stroke="var(--accent)" strokeWidth="1.3" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
      <rect x="8.5" y="19" width="5" height="1.5" rx="0.75" fill="var(--accent)" opacity="0.6"/>
    </svg>
  ),
}

/* ── Nav item ───────────────────────────────────────────────────────────────── */
function SideNavItem({ to, icon, label, badge }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) => `lq-nav-item${isActive ? ' active' : ''}`}
    >
      <span style={{ flexShrink: 0, display: 'flex' }}>{icon}</span>
      <span style={{ flex: 1 }}>{label}</span>
      {badge > 0 && (
        <span style={{
          background: 'var(--amber)',
          color: '#000',
          fontSize: '10px',
          fontWeight: 800,
          borderRadius: '10px',
          padding: '1px 6px',
          lineHeight: '16px',
        }}>
          {badge > 9 ? '9+' : badge}
        </span>
      )}
    </NavLink>
  )
}

/* ── Sidebar ────────────────────────────────────────────────────────────────── */
function Sidebar({ open, onClose, pendingCount }) {
  return (
    <aside className={`lq-sidebar${open ? ' open' : ''}`}>
      {/* Logo */}
      <div style={{ padding: '22px 20px 18px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {Icon.scale}
          <div>
            <div style={{
              fontWeight: 900,
              fontSize: '16px',
              letterSpacing: '-0.03em',
              color: 'var(--text-1)',
              lineHeight: 1.1,
            }}>
              LIQUET
            </div>
            <div style={{ fontSize: '10px', color: 'var(--text-3)', letterSpacing: '0.06em', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
              DISPUTE ARBITER
            </div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: '10px 10px', overflowY: 'auto' }}>
        <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-3)', letterSpacing: '0.10em', padding: '6px 11px 4px', textTransform: 'uppercase', marginBottom: '2px' }}>
          Operations
        </div>
        <SideNavItem to="/dashboard"  icon={Icon.dashboard}  label="Dashboard" />
        <SideNavItem to="/analytics"  icon={Icon.analytics}  label="Analytics" />
        <SideNavItem to="/automation" icon={Icon.automation} label="Automation" />
        <SideNavItem to="/queue"      icon={Icon.queue}      label="NON LIQUET Queue" badge={pendingCount} />

        <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-3)', letterSpacing: '0.10em', padding: '16px 11px 4px', textTransform: 'uppercase', marginBottom: '2px' }}>
          Insight
        </div>
        <SideNavItem to="/seller-risk" icon={Icon.risk}     label="Seller Risk" />
        <SideNavItem to="/timeline"    icon={Icon.timeline} label="Timeline" />
        <SideNavItem to="/policy"      icon={Icon.policy}   label="Policy Browser" />
      </nav>

      {/* New Dispute CTA */}
      <div style={{ padding: '12px 12px', borderTop: '1px solid var(--border)' }}>
        <NavLink
          to="/new"
          className={({ isActive }) => `lq-btn lq-btn-primary${isActive ? '' : ''}`}
          style={{ width: '100%', justifyContent: 'center' }}
        >
          {Icon.plus}
          New Dispute
        </NavLink>
      </div>

      {/* Status footer */}
      <div style={{ padding: '10px 16px 14px', borderTop: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
          <span style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center', width: 10, height: 10 }}>
            <span style={{ position: 'absolute', inset: 0, borderRadius: '50%', background: 'var(--green)', opacity: 0.4 }} className="lq-ping" />
            <span className="lq-dot lq-dot-resolved" />
          </span>
          <span style={{ fontSize: '11px', color: 'var(--text-2)' }}>QwenCloud · Alibaba ECS</span>
        </div>
      </div>
    </aside>
  )
}

/* ── Pending count hook ──────────────────────────────────────────────────────── */
function usePendingCount() {
  const [count, setCount] = React.useState(0)
  useEffect(() => {
    const refresh = () =>
      fetch('/api/disputes/?status=open')
        .then(r => r.json())
        .then(d => setCount(Array.isArray(d) ? d.length : 0))
        .catch(() => {})
    refresh()
    const id = setInterval(refresh, 30000)
    return () => clearInterval(id)
  }, [])
  return count
}

/* ── App shell ──────────────────────────────────────────────────────────────── */
function AppShell({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const pendingCount = usePendingCount()
  const location = useLocation()

  useEffect(() => { setSidebarOpen(false) }, [location.pathname])

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* Mobile overlay — only shown when sidebar is open on small screens */}
      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          style={{
            position: 'fixed', inset: 0,
            background: 'rgba(15,23,42,0.35)',
            zIndex: 49,
          }}
        />
      )}

      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} pendingCount={pendingCount} />

      <div className="lq-content" style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
        {/* Mobile topbar — visible below lg breakpoint via CSS */}
        <div style={{
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '14px 18px',
          borderBottom: '1px solid var(--border)',
          background: 'var(--bg-surface)',
          position: 'sticky',
          top: 0,
          zIndex: 30,
        }} className="lq-mobile-topbar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {Icon.scale}
            <span style={{ fontWeight: 900, fontSize: '15px', letterSpacing: '-0.03em' }}>LIQUET</span>
          </div>
          <button
            onClick={() => setSidebarOpen(o => !o)}
            style={{ background: 'none', border: 'none', color: 'var(--text-2)', cursor: 'pointer', padding: '4px' }}
            aria-label="Toggle menu"
          >
            {sidebarOpen ? Icon.close : Icon.hamburger}
          </button>
        </div>

        {/* Page content with route-keyed animation */}
        <main style={{ flex: 1, padding: '28px 32px' }}>
          <div key={location.pathname} className="lq-slide-up">
            {children}
          </div>
        </main>

        <footer style={{
          padding: '14px 32px',
          borderTop: '1px solid var(--border)',
          fontSize: '11px',
          color: 'var(--text-3)',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontFamily: 'var(--font-mono)',
        }}>
          <span>LIQUET</span>
          <span style={{ color: 'var(--text-3)', opacity: 0.4 }}>·</span>
          <span>QwenCloud Global AI Hackathon</span>
          <span style={{ color: 'var(--text-3)', opacity: 0.4 }}>·</span>
          <em style={{ fontStyle: 'italic' }}>liquet</em>
          <span>&nbsp;—&nbsp;"it is clear"</span>
        </footer>
      </div>
    </div>
  )
}

/* ── Root ───────────────────────────────────────────────────────────────────── */
export default function App() {
  const location = useLocation()

  if (location.pathname === '/') {
    return (
      <Routes>
        <Route path="/" element={<Landing />} />
      </Routes>
    )
  }

  return (
    <AppShell>
      <Routes>
        <Route path="/dashboard"          element={<Dashboard />} />
        <Route path="/cases/:disputeId"   element={<CaseDetail />} />
        <Route path="/queue"              element={<NonLiquetQueue />} />
        <Route path="/seller-risk"        element={<SellerRisk />} />
        <Route path="/analytics"          element={<Analytics />} />
        <Route path="/automation"         element={<Automation />} />
        <Route path="/policy"             element={<PolicyBrowser />} />
        <Route path="/timeline"           element={<Timeline />} />
        <Route path="/new"                element={<NewDispute />} />
      </Routes>
    </AppShell>
  )
}
