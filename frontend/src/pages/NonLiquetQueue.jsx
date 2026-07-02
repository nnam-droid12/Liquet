import React, { useEffect, useState } from 'react'

function ReviewCard({ brief, onResolve }) {
  const [action, setAction] = useState(brief.leaning_verdict)
  const [note, setNote] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handle = async () => {
    setSubmitting(true)
    await onResolve(brief.decision_id, action, note)
    setSubmitting(false)
  }

  const RESOLUTIONS = ['full_refund', 'partial_refund', 'replacement', 'return_then_refund', 'deny']

  return (
    <div className="bg-white rounded-xl shadow-sm border-2 border-amber-300 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <span className="font-mono text-xs text-gray-400">{brief.dispute_id.slice(0, 8)}</span>
          <h3 className="font-bold text-gray-900 mt-0.5 capitalize">{brief.dispute_type.replace(/_/g, ' ')}</h3>
        </div>
        <div className="text-right">
          <div className="text-xs text-gray-400">Order Value</div>
          <div className="font-bold text-gray-800">${brief.order_value?.toFixed(2)}</div>
        </div>
      </div>

      {/* Why NON LIQUET */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4 text-sm">
        <div className="text-xs font-bold text-amber-700 uppercase mb-1">Why NON LIQUET</div>
        <div className="text-amber-900">{brief.abstention_reason}</div>
      </div>

      {/* Narratives */}
      <div className="grid md:grid-cols-2 gap-3 mb-4">
        <div className="bg-blue-50 rounded-lg p-3">
          <div className="text-xs font-bold text-blue-700 mb-1">Buyer</div>
          <p className="text-xs text-gray-700">{brief.buyer_narrative}</p>
        </div>
        <div className="bg-orange-50 rounded-lg p-3">
          <div className="text-xs font-bold text-orange-700 mb-1">Seller</div>
          <p className="text-xs text-gray-700">{brief.seller_narrative}</p>
        </div>
      </div>

      {/* Evidence summary */}
      {brief.evidence_summary?.length > 0 && (
        <details className="mb-4">
          <summary className="cursor-pointer text-xs text-gray-500 hover:text-gray-700 font-medium">
            View {brief.evidence_summary.length} evidence items
          </summary>
          <div className="mt-2 space-y-1">
            {brief.evidence_summary.map(ev => (
              <div key={ev.id} className="text-xs bg-gray-50 border border-gray-100 rounded p-2">
                <span className="font-mono text-gray-400">[{ev.id}]</span>{' '}
                <span className="font-medium text-gray-600">{ev.source}</span>{' '}
                <span className="text-gray-400">·  rel {Math.round(ev.reliability * 100)}%</span>{' '}
                <span className="text-gray-500">{ev.summary}</span>
              </div>
            ))}
          </div>
        </details>
      )}

      {/* Agent's leaning */}
      <div className="bg-gray-50 rounded-lg p-3 mb-4 flex items-center gap-3">
        <div className="text-sm text-gray-600">
          Agent leans towards{' '}
          <span className="font-bold capitalize">{brief.leaning_verdict?.replace(/_/g, ' ')}</span>
          {' '}with <span className="font-bold">{Math.round(brief.leaning_confidence * 100)}%</span> confidence
        </div>
      </div>

      {/* Hard contradictions */}
      {brief.hard_contradictions?.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 text-xs text-red-800">
          <strong>Hard contradictions:</strong> {brief.hard_contradictions.join('; ')}
        </div>
      )}

      {/* Human action */}
      <div className="border-t border-gray-200 pt-4">
        <div className="text-xs font-bold text-gray-500 uppercase mb-2">Human Decision</div>
        <div className="flex flex-wrap gap-2 mb-3">
          {RESOLUTIONS.map(r => (
            <button
              key={r}
              onClick={() => setAction(r)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium border transition-colors ${
                action === r
                  ? 'bg-blue-700 text-white border-blue-700'
                  : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
              }`}
            >
              {r.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
        <input
          type="text"
          placeholder="Override note (optional)"
          value={note}
          onChange={e => setNote(e.target.value)}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={handle}
          disabled={submitting}
          className="w-full bg-blue-700 text-white py-2 rounded-md text-sm font-medium hover:bg-blue-800 disabled:opacity-50 transition-colors"
        >
          {submitting ? 'Submitting…' : `Confirm: ${action.replace(/_/g, ' ')}`}
        </button>
      </div>
    </div>
  )
}

export default function NonLiquetQueue() {
  const [queue, setQueue] = useState([])
  const [loading, setLoading] = useState(true)
  const [resolved, setResolved] = useState([])
  const [typeFilter, setTypeFilter] = useState('all')
  const [sortBy, setSortBy] = useState('value')

  const load = () => {
    fetch('/api/queue/')
      .then(r => r.json())
      .then(data => { setQueue(data); setLoading(false) })
      .catch(() => setLoading(false))
  }

  useEffect(load, [])

  const handleResolve = async (decisionId, resolution, note) => {
    await fetch(`/api/queue/${decisionId}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        reviewer_id: 'human-reviewer-1',
        approved_resolution: resolution,
        override_note: note || null,
      }),
    })
    setResolved(r => [...r, decisionId])
    setQueue(q => q.filter(b => b.decision_id !== decisionId))
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">NON LIQUET Queue</h1>
        <p className="text-gray-500 text-sm mt-1">
          Cases the agent could not confidently resolve. Review each brief and confirm a decision.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3 mb-4">
        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-100 text-amber-700 border border-amber-300 rounded-md font-bold text-sm">
          ⚠ NON LIQUET — {queue.length} pending
        </span>
        {resolved.length > 0 && (
          <span className="text-sm text-green-600">✓ {resolved.length} resolved this session</span>
        )}
      </div>

      {/* Filter + sort controls */}
      {queue.length > 0 && (() => {
        const types = ['all', ...new Set(queue.map(b => b.dispute_type))]
        const visibleQueue = queue
          .filter(b => typeFilter === 'all' || b.dispute_type === typeFilter)
          .sort((a, b) => sortBy === 'value'
            ? (b.order_value || 0) - (a.order_value || 0)
            : (b.leaning_confidence || 0) - (a.leaning_confidence || 0))

        return (
          <>
            <div className="flex flex-wrap gap-2 mb-4">
              <div className="flex gap-1 flex-wrap">
                {types.map(t => (
                  <button
                    key={t}
                    onClick={() => setTypeFilter(t)}
                    className={`text-xs px-2 py-1 rounded border transition-colors ${
                      typeFilter === t
                        ? 'bg-blue-700 text-white border-blue-700'
                        : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {t === 'all' ? 'All types' : t.replace(/_/g, ' ')}
                  </button>
                ))}
              </div>
              <div className="ml-auto flex gap-1">
                {['value', 'confidence'].map(s => (
                  <button
                    key={s}
                    onClick={() => setSortBy(s)}
                    className={`text-xs px-2 py-1 rounded border transition-colors ${
                      sortBy === s
                        ? 'bg-gray-800 text-white border-gray-800'
                        : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    Sort: {s}
                  </button>
                ))}
              </div>
            </div>
            <div className="space-y-6">
              {visibleQueue.map(brief => (
                <ReviewCard key={brief.decision_id} brief={brief} onResolve={handleResolve} />
              ))}
            </div>
          </>
        )
      })()}

      {loading && <div className="text-gray-500 text-center py-8">Loading queue…</div>}

      {!loading && queue.length === 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <div className="text-4xl mb-3">⚖️</div>
          <div className="text-gray-500">
            {resolved.length > 0
              ? `All ${resolved.length} cases resolved. The queue is clear.`
              : 'No cases in the NON LIQUET queue. All disputes are either resolved or pending investigation.'}
          </div>
        </div>
      )}
    </div>
  )
}
