import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { SkeletonStatGrid, SkeletonTableRows } from '../components/Skeleton.jsx'

function relativeAge(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${Math.max(mins, 1)}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}d ago`
  return new Date(dateStr).toLocaleDateString()
}

const STATUS_COLOR = {
  open: 'bg-yellow-100 text-yellow-800',
  investigating: 'bg-blue-100 text-blue-800 animate-pulse',
  resolved: 'bg-green-100 text-green-800',
  escalated: 'bg-red-100 text-red-800',
  closed: 'bg-gray-100 text-gray-600',
  failed: 'bg-red-200 text-red-900',
}

const GATE_BADGE = {
  LIQUET: 'bg-green-100 text-green-700 border border-green-300',
  NON_LIQUET: 'bg-amber-100 text-amber-700 border border-amber-300',
}

function StatCard({ label, value, sub, accent }) {
  const colors = {
    gray: 'text-gray-700',
    yellow: 'text-yellow-700',
    green: 'text-green-700',
    red: 'text-red-700',
    blue: 'text-blue-700',
    purple: 'text-purple-700',
  }
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className={`text-3xl font-bold ${colors[accent] || 'text-gray-700'}`}>{value}</div>
      <div className="text-gray-500 text-sm mt-0.5">{label}</div>
      {sub && <div className="text-xs text-gray-400 mt-1">{sub}</div>}
    </div>
  )
}

function AutoResolutionBar({ rate }) {
  const pct = Math.round(rate * 100)
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="flex items-end justify-between mb-2">
        <div>
          <div className="text-3xl font-bold text-emerald-600">{pct}%</div>
          <div className="text-gray-500 text-sm">Auto-Resolution Rate</div>
        </div>
        <div className="text-xs text-gray-400 text-right">
          <div>LIQUET decisions</div>
          <div>without human review</div>
        </div>
      </div>
      <div className="bg-gray-100 rounded-full h-2">
        <div
          className="bg-emerald-500 h-2 rounded-full transition-all duration-700"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [disputes, setDisputes] = useState([])
  const [platformStats, setPlatformStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('')
  const [search, setSearch] = useState('')

  const refresh = React.useCallback(() => {
    Promise.all([
      fetch('/api/disputes/').then(r => r.json()),
      fetch('/api/stats').then(r => r.ok ? r.json() : null).catch(() => null),
    ]).then(([disputeData, statsData]) => {
      setDisputes(disputeData)
      setPlatformStats(statsData)
      setLoading(false)
    }).catch(e => { setError(e.message); setLoading(false) })
  }, [])

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, 15000)
    return () => clearInterval(id)
  }, [refresh])

  const filtered = disputes
    .filter(d => !filter || d.status === filter)
    .filter(d => !search || d.order_id.toLowerCase().includes(search.toLowerCase()) ||
      d.id.toLowerCase().includes(search.toLowerCase()) ||
      d.dispute_type.includes(search.toLowerCase()))

  const localStats = {
    total: disputes.length,
    open: disputes.filter(d => d.status === 'open').length,
    resolved: disputes.filter(d => d.status === 'resolved').length,
    escalated: disputes.filter(d => d.status === 'escalated').length,
    investigating: disputes.filter(d => d.status === 'investigating').length,
  }

  const autoRate = platformStats?.auto_resolution_rate || (
    localStats.resolved / Math.max(localStats.resolved + localStats.escalated, 1)
  )
  const avgConf = platformStats ? Math.round(platformStats.avg_confidence * 100) : 0

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dispute Dashboard</h1>
          <p className="text-gray-500 text-sm mt-1">
            LIQUET resolves autonomously · NON LIQUET escalates to human review
          </p>
        </div>
        <Link
          to="/new"
          className="bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-800 transition-colors"
        >
          + New Dispute
        </Link>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        <StatCard label="Total" value={localStats.total} accent="gray" />
        <StatCard label="Open" value={localStats.open} accent="yellow" />
        <StatCard label="Investigating" value={localStats.investigating} accent="blue" />
        <StatCard label="Resolved" value={localStats.resolved} accent="green" sub="LIQUET" />
        <StatCard label="Escalated" value={localStats.escalated} accent="red" sub="NON LIQUET" />
        <StatCard label="Avg Confidence" value={avgConf ? `${avgConf}%` : '—'} accent="purple" />
      </div>

      {/* Auto-resolution rate + type breakdown */}
      {(localStats.resolved + localStats.escalated) > 0 && (
        <div className="grid md:grid-cols-2 gap-4 mb-6">
          <AutoResolutionBar rate={autoRate} />
          {platformStats?.dispute_type_breakdown && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="text-sm font-medium text-gray-600 mb-3">Dispute Type Breakdown</div>
              <div className="space-y-2">
                {Object.entries(platformStats.dispute_type_breakdown)
                  .sort((a, b) => b[1] - a[1])
                  .map(([type, count]) => {
                    const total = Object.values(platformStats.dispute_type_breakdown).reduce((a, b) => a + b, 0)
                    const pct = Math.round(count / total * 100)
                    return (
                      <div key={type}>
                        <div className="flex justify-between text-xs text-gray-500 mb-0.5">
                          <span className="capitalize">{type.replace(/_/g, ' ')}</span>
                          <span className="font-medium">{count} ({pct}%)</span>
                        </div>
                        <div className="bg-gray-100 rounded-full h-1.5">
                          <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    )
                  })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Search + Filter */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <input
          type="text"
          placeholder="Search by order ID or dispute type…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="flex-1 border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <div className="flex gap-2 flex-wrap">
          {['', 'open', 'investigating', 'resolved', 'escalated'].map(s => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`px-3 py-1 rounded-full text-sm font-medium border transition-colors ${
                filter === s
                  ? 'bg-blue-700 text-white border-blue-700'
                  : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
              }`}
            >
              {s || 'All'}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      {loading && <><SkeletonStatGrid /><SkeletonTableRows /></>}
      {error && <div className="text-red-600 text-center py-8">Error: {error}</div>}
      {!loading && !error && filtered.length === 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center text-gray-400">
          No disputes found.{' '}
          <Link to="/new" className="text-blue-600 underline">Create one</Link> to get started.
        </div>
      )}
      {!loading && !error && filtered.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-700">ID</th>
                <th className="text-left px-4 py-3 font-medium text-gray-700">Order</th>
                <th className="text-left px-4 py-3 font-medium text-gray-700">Type</th>
                <th className="text-left px-4 py-3 font-medium text-gray-700">Status</th>
                <th className="text-left px-4 py-3 font-medium text-gray-700">Gate</th>
                <th className="text-left px-4 py-3 font-medium text-gray-700">Created</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map(d => (
                <tr key={d.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">{d.id.slice(0, 8)}</td>
                  <td className="px-4 py-3 font-medium">{d.order_id}</td>
                  <td className="px-4 py-3 text-gray-600 capitalize">{d.dispute_type.replace(/_/g, ' ')}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLOR[d.status] || 'bg-gray-100 text-gray-600'}`}>
                      {d.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {d.status === 'resolved' && (
                      <span className={`px-2 py-0.5 rounded text-xs font-bold ${GATE_BADGE.LIQUET}`}>LIQUET</span>
                    )}
                    {d.status === 'escalated' && (
                      <span className={`px-2 py-0.5 rounded text-xs font-bold ${GATE_BADGE.NON_LIQUET}`}>NON LIQUET</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs" title={new Date(d.created_at).toLocaleString()}>
                    {relativeAge(d.created_at)}
                  </td>
                  <td className="px-4 py-3">
                    <Link to={`/cases/${d.id}`} className="text-blue-600 hover:text-blue-800 font-medium text-xs">
                      View →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
