import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'

function ConfidenceBar({ value }) {
  const pct = Math.round(value * 100)
  const color = value >= 0.80 ? 'bg-green-500' : value >= 0.60 ? 'bg-yellow-500' : 'bg-red-400'
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 bg-gray-200 rounded-full h-2">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm font-bold text-gray-700">{pct}%</span>
    </div>
  )
}

function GateBadge({ gate }) {
  if (gate === 'LIQUET') {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-green-100 text-green-800 border border-green-300 font-bold text-sm">
        <span className="text-green-600">✓</span> LIQUET — Auto-Resolved
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-amber-100 text-amber-800 border border-amber-300 font-bold text-sm">
      <span className="text-amber-500">⚠</span> NON LIQUET — Human Review Required
    </span>
  )
}

function EvidenceCard({ ev }) {
  const typeColor = {
    carrier_scan: 'bg-green-50 border-green-200',
    order_record: 'bg-blue-50 border-blue-200',
    listing_data: 'bg-indigo-50 border-indigo-200',
    photo: 'bg-purple-50 border-purple-200',
    message: 'bg-gray-50 border-gray-200',
    user_claim: 'bg-red-50 border-red-200',
  }
  const reliabilityColor = ev.reliability >= 0.85 ? 'text-green-600' : ev.reliability >= 0.60 ? 'text-yellow-600' : 'text-red-500'

  return (
    <div className={`rounded-lg border p-3 text-xs ${typeColor[ev.evidence_type] || 'bg-gray-50 border-gray-200'}`}>
      <div className="flex items-center justify-between mb-1">
        <span className="font-semibold text-gray-700">[{ev.id}] {ev.source}</span>
        <span className={`font-bold ${reliabilityColor}`}>reliability {Math.round(ev.reliability * 100)}%</span>
      </div>
      <div className="text-gray-500 uppercase tracking-wide text-[10px] mb-1">{ev.evidence_type.replace(/_/g, ' ')}</div>
      <div className="text-gray-700 line-clamp-3">{typeof ev.content === 'string' ? ev.content : JSON.stringify(ev.content).slice(0, 200)}</div>
    </div>
  )
}

export default function CaseDetail() {
  const { disputeId } = useParams()
  const [dispute, setDispute] = useState(null)
  const [caseFile, setCaseFile] = useState(null)
  const [decision, setDecision] = useState(null)
  const [audit, setAudit] = useState([])
  const [loading, setLoading] = useState(true)
  const [investigating, setInvestigating] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const [d, c, dec, a] = await Promise.allSettled([
        fetch(`/api/disputes/${disputeId}`).then(r => r.json()),
        fetch(`/api/cases/${disputeId}/casefile`).then(r => r.ok ? r.json() : null),
        fetch(`/api/cases/${disputeId}/decision`).then(r => r.ok ? r.json() : null),
        fetch(`/api/cases/${disputeId}/audit`).then(r => r.ok ? r.json() : []),
      ])
      if (d.status === 'fulfilled') setDispute(d.value)
      if (c.status === 'fulfilled') setCaseFile(c.value)
      if (dec.status === 'fulfilled') setDecision(dec.value)
      if (a.status === 'fulfilled') setAudit(a.value || [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [disputeId])

  const handleInvestigate = async () => {
    setInvestigating(true)
    await fetch(`/api/disputes/${disputeId}/investigate`, { method: 'POST' })
    await load()
    setInvestigating(false)
  }

  if (loading) return <div className="text-gray-500 text-center py-12">Loading case…</div>
  if (!dispute) return <div className="text-red-500 text-center py-12">Dispute not found</div>

  return (
    <div>
      {/* Breadcrumb */}
      <div className="mb-4 text-sm text-gray-500">
        <Link to="/" className="hover:text-blue-600">Dashboard</Link>
        <span className="mx-2">›</span>
        <span className="text-gray-800 font-medium">Case {disputeId.slice(0, 8)}</span>
      </div>

      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">{dispute.order_id}</h1>
            <p className="text-gray-500 text-sm mt-0.5 capitalize">{dispute.dispute_type.replace(/_/g, ' ')} · {dispute.status}</p>
          </div>
          <div className="flex flex-col items-end gap-2">
            {decision && <GateBadge gate={decision.gate_result} />}
            {!decision && dispute.status === 'open' && (
              <button
                onClick={handleInvestigate}
                disabled={investigating}
                className="bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-800 disabled:opacity-50"
              >
                {investigating ? 'Investigating…' : '⚡ Run Autopilot'}
              </button>
            )}
          </div>
        </div>

        {/* Narratives */}
        <div className="grid md:grid-cols-2 gap-4 mt-6">
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="text-xs font-bold text-blue-700 uppercase mb-2">Buyer's Account</div>
            <p className="text-sm text-gray-700">{dispute.buyer_narrative}</p>
          </div>
          <div className="bg-orange-50 rounded-lg p-4">
            <div className="text-xs font-bold text-orange-700 uppercase mb-2">Seller's Account</div>
            <p className="text-sm text-gray-700">{dispute.seller_narrative || <em className="text-gray-400">No response yet</em>}</p>
          </div>
        </div>
      </div>

      {/* Verdict */}
      {decision && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="font-bold text-gray-900 mb-4">Verdict</h2>
          <div className="grid md:grid-cols-3 gap-4 mb-4">
            <div>
              <div className="text-xs text-gray-500 mb-1">Resolution</div>
              <div className="font-bold text-gray-800 capitalize">{decision.verdict.resolution.replace(/_/g, ' ')}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-1">Confidence</div>
              <ConfidenceBar value={decision.verdict.confidence} />
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-1">Value at Stake</div>
              <div className="font-bold text-gray-800">${decision.verdict.value_at_stake?.toFixed(2)}</div>
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-700">
            <div className="text-xs font-bold text-gray-500 uppercase mb-2">Rationale</div>
            {decision.verdict.rationale}
          </div>
          {decision.verdict.policy_clauses?.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1">
              {decision.verdict.policy_clauses.map(c => (
                <span key={c} className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded font-mono">{c}</span>
              ))}
            </div>
          )}
          {decision.abstention_reason && (
            <div className="mt-4 bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800">
              <div className="font-bold mb-1">Why NON LIQUET</div>
              {decision.abstention_reason}
            </div>
          )}
        </div>
      )}

      {/* Evidence */}
      {caseFile && caseFile.evidence?.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="font-bold text-gray-900 mb-4">
            Evidence ({caseFile.evidence.length} items)
            <span className="ml-2 text-xs text-gray-400 font-normal">sorted by reliability</span>
          </h2>
          <div className="grid md:grid-cols-2 gap-3">
            {[...caseFile.evidence].sort((a, b) => b.reliability - a.reliability).map(ev => (
              <EvidenceCard key={ev.id} ev={ev} />
            ))}
          </div>
          {caseFile.hard_contradictions?.length > 0 && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800">
              <div className="font-bold mb-1">Hard Contradiction</div>
              {caseFile.hard_contradictions.join(' | ')}
            </div>
          )}
        </div>
      )}

      {/* Audit trail */}
      {audit.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="font-bold text-gray-900 mb-4">Audit Trail</h2>
          <div className="space-y-2">
            {audit.map(e => (
              <div key={e.id} className="flex gap-3 text-sm">
                <span className="text-gray-400 text-xs font-mono w-28 shrink-0 pt-0.5">
                  {new Date(e.timestamp).toLocaleTimeString()}
                </span>
                <span className={`text-xs px-1.5 py-0.5 rounded font-medium shrink-0 h-fit ${
                  e.actor === 'agent' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'
                }`}>{e.actor}</span>
                <div>
                  <span className="font-medium text-gray-800">{e.event}</span>
                  {Object.keys(e.data || {}).length > 0 && (
                    <div className="text-gray-500 text-xs mt-0.5">{JSON.stringify(e.data)}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
