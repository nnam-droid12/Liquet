import React from 'react'
import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import Landing from './pages/Landing.jsx'
import Dashboard from './pages/Dashboard.jsx'
import CaseDetail from './pages/CaseDetail.jsx'
import NonLiquetQueue from './pages/NonLiquetQueue.jsx'
import NewDispute from './pages/NewDispute.jsx'

function NavItem({ to, children }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `px-4 py-2 rounded-md text-sm font-medium transition-colors ${
          isActive
            ? 'bg-blue-700 text-white'
            : 'text-blue-100 hover:bg-blue-600 hover:text-white'
        }`
      }
    >
      {children}
    </NavLink>
  )
}

function AppShell({ children }) {
  return (
    <div className="min-h-screen flex flex-col">
      <nav className="bg-blue-800 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <NavLink to="/" className="text-white font-bold text-xl tracking-tight hover:text-blue-100">
                LIQUET
              </NavLink>
              <span className="text-blue-300 text-xs font-mono hidden sm:block">
                Autonomous Dispute Resolution
              </span>
            </div>
            <div className="flex gap-2">
              <NavItem to="/dashboard">Dashboard</NavItem>
              <NavItem to="/queue">Non-Liquet Queue</NavItem>
              <NavItem to="/new">New Dispute</NavItem>
            </div>
          </div>
        </div>
      </nav>

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      <footer className="bg-white border-t border-gray-200 py-4 text-center text-xs text-gray-400">
        Liquet — Autonomous Marketplace Dispute Resolution &nbsp;|&nbsp;
        QwenCloud Global AI Hackathon &nbsp;|&nbsp;
        <em>liquet</em> ("it is clear") &nbsp;·&nbsp; <em>non liquet</em> ("it is not clear")
      </footer>
    </div>
  )
}

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
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/cases/:disputeId" element={<CaseDetail />} />
        <Route path="/queue" element={<NonLiquetQueue />} />
        <Route path="/new" element={<NewDispute />} />
      </Routes>
    </AppShell>
  )
}
