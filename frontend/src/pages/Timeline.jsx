import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

const STATUS_ICON = {
  open: '○',
  investigating: '⟳',
  resolved: '✓',
  escalated: '⚠',
  closed: '—',
  failed: '✕',
}

const STATUS_COLOR = {
  open: 'text-yellow-600 border-yellow-400 bg-yellow-50',
  investigating: 'text-blue-600 border-blue-400 bg-blue-50 animate-pulse',
  resolved: 'text-green-700 border-green-500 bg-green-50',
  escalated: 'text-amber-700 border-amber-500 bg-amber-50',
  closed: 'text-gray-500 border-gray-300 bg-gray-50',
  failed: 'text-red-600 border-red-400 bg-red-50',
}

function relativeAge(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${Math.max(mins, 1)}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

export default function Timeline() {
  const [disputes, setDisputes] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/disputes/')
      .then(r => r.json())
      .then(data => {
        setDisputes([...data].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)))
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Case Timeline</h1>
        <p className="text-gray-500 text-sm mt-1">All disputes in chronological order, most recent first</p>
      </div>

      {loading && <div className="text-gray-400 text-center py-12">Loading timeline…</div>}

      {!loading && disputes.length === 0 && (
        <div className="text-gray-400 text-center py-12">No disputes yet.</div>
      )}

      <div className="relative">
        <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gray-200" />
        <div className="space-y-4">
          {disputes.map(d => (
            <div key={d.id} className="relative flex gap-4 items-start">
              <div className={`relative z-10 w-10 h-10 rounded-full border-2 flex items-center justify-center text-sm font-bold shrink-0 ${STATUS_COLOR[d.status] || 'bg-gray-50 border-gray-300 text-gray-600'}`}>
                {STATUS_ICON[d.status] || '?'}
              </div>
              <div className="flex-1 bg-white rounded-xl border border-gray-200 p-4 shadow-sm min-w-0">
                <div className="flex items-start justify-between gap-2 flex-wrap">
                  <div>
                    <Link
                      to={`/cases/${d.id}`}
                      className="font-semibold text-gray-800 hover:text-blue-700 text-sm"
                    >
                      {d.order_id}
                    </Link>
                    <span className="ml-2 text-xs capitalize text-gray-500">
                      {d.dispute_type.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <span className="text-xs text-gray-400" title={new Date(d.created_at).toLocaleString()}>
                    {relativeAge(d.created_at)}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1 line-clamp-2">{d.buyer_narrative}</p>
                <div className="flex items-center gap-2 mt-2">
                  <span className={`text-xs font-medium px-1.5 py-0.5 rounded border ${STATUS_COLOR[d.status]}`}>
                    {d.status}
                  </span>
                  <span className="text-xs text-gray-400 font-mono">{d.id.slice(0, 8)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
