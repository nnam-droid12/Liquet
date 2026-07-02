import React, { useEffect, useState } from 'react'

export default function DigestWidget() {
  const [digest, setDigest] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/digest/daily')
      .then(r => r.ok ? r.json() : null)
      .then(d => { setDigest(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-40 mb-3" />
      <div className="h-3 bg-gray-100 rounded w-full mb-2" />
      <div className="h-3 bg-gray-100 rounded w-3/4" />
    </div>
  )

  if (!digest) return null

  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border border-blue-200 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-bold text-gray-800 text-sm">24h Digest</h3>
        <span className="text-xs text-gray-400">
          {new Date(digest.generated_at).toLocaleTimeString()}
        </span>
      </div>
      <p className="text-sm text-gray-700 mb-4 leading-relaxed">{digest.summary}</p>
      <div className="grid grid-cols-3 gap-3">
        <div className="text-center">
          <div className="text-2xl font-black text-blue-700">{digest.new_disputes}</div>
          <div className="text-xs text-gray-500">New</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-black text-emerald-700">{digest.auto_resolved}</div>
          <div className="text-xs text-gray-500">LIQUET</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-black text-amber-700">{digest.escalated}</div>
          <div className="text-xs text-gray-500">Escalated</div>
        </div>
      </div>
    </div>
  )
}
