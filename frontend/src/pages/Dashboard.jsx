import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

const STATUS_COLOR = {
  open: 'bg-yellow-100 text-yellow-800',
  investigating: 'bg-blue-100 text-blue-800',
  resolved: 'bg-green-100 text-green-800',
  escalated: 'bg-red-100 text-red-800',
  closed: 'bg-gray-100 text-gray-600',
}

const GATE_BADGE = {
  LIQUET: 'bg-green-100 text-green-700 border border-green-300',
  NON_LIQUET: 'bg-amber-100 text-amber-700 border border-amber-300',
}

export default function Dashboard() {
  const [disputes, setDisputes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('')

  useEffect(() => {
    fetch('/api/disputes/')
      .then(r => r.json())
      .then(data => { setDisputes(data); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [])

  const filtered = filter
    ? disputes.filter(d => d.status === filter)
    : disputes

  const stats = {
    total: disputes.length,
    open: disputes.filter(d => d.status === 'open').length,
    resolved: disputes.filter(d => d.status === 'resolved').length,
    escalated: disputes.filter(d => d.status === 'escalated').length,
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dispute Dashboard</h1>
          <p className="text-gray-500 text-sm mt-1">All marketplace disputes — LIQUET resolves autonomously, NON LIQUET awaits human review</p>
        </div>
        <Link to="/new" className="bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-800 transition-colors">
          + New Dispute
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Total', value: stats.total, color: 'text-gray-700' },
          { label: 'Open', value: stats.open, color: 'text-yellow-700' },
          { label: 'Resolved', value: stats.resolved, color: 'text-green-700' },
          { label: 'Escalated', value: stats.escalated, color: 'text-red-700' },
        ].map(s => (
          <div key={s.label} className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className={`text-3xl font-bold ${s.color}`}>{s.value}</div>
            <div className="text-gray-500 text-sm">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Filter */}
      <div className="flex gap-2 mb-4">
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

      {/* Table */}
      {loading && <div className="text-gray-500 text-center py-8">Loading disputes…</div>}
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
                <th className="text-left px-4 py-3 font-medium text-gray-700">Verdict</th>
                <th className="text-left px-4 py-3 font-medium text-gray-700">Created</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map(d => (
                <tr key={d.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">{d.id.slice(0, 8)}</td>
                  <td className="px-4 py-3 font-medium">{d.order_id}</td>
                  <td className="px-4 py-3 text-gray-600">{d.dispute_type.replace(/_/g, ' ')}</td>
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
                  <td className="px-4 py-3 text-gray-400 text-xs">
                    {new Date(d.created_at).toLocaleDateString()}
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
