import React, { useEffect, useRef, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import GhostCasesPanel from '../components/GhostCasesPanel.jsx'
import StabilityGauge from '../components/StabilityGauge.jsx'
import SkepticPanel from '../components/SkepticPanel.jsx'
import ConfidenceBreakdown from '../components/ConfidenceBreakdown.jsx'
import AuditTimeline from '../components/AuditTimeline.jsx'
import SellerReplyForm from '../components/SellerReplyForm.jsx'

function ConfidenceBar({ value }) {
  const pct = Math.round(value * 100)
  const color = value >= 0.80 ? 'bg-green-500' : value >= 0.60 ? 'bg-yellow-500' : 'bg-red-400'
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 bg-gray-200 rounded-full h-2">
        <div className={`h-2 rounded-full transition-all duration-500 ${color}`} style={{ width: `${pct}%` }} />
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

function CopyButton({ text, label }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1800)
    })
  }
  return (
    <button
      onClick={copy}
      className="text-xs text-gray-400 hover:text-gray-600 transition-colors ml-1"
      title={`Copy ${label}`}
    >
      {copied ? '✓' : '⎘'}
    </button>
  )
}

const EVIDENCE_TYPES = ['all', 'carrier_scan', 'order_record', 'listing_data', 'photo', 'message', 'user_claim']

function EvidenceSection({ evidence, hardContradictions }) {
  const [filter, setFilter] = useState('all')
  const types = EVIDENCE_TYPES.filter(t => t === 'all' || evidence.some(e => e.evidence_type === t))
  const filtered = filter === 'all' ? evidence : evidence.filter(e => e.evidence_type === filter)
  const sorted = [...filtered].sort((a, b) => b.reliability - a.reliability)

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
      <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
        <h2 className="font-bold text-gray-900">
          Evidence
          <span className="ml-2 text-gray-400 font-normal text-sm">({sorted.length}/{evidence.length})</span>
        </h2>
        <div className="flex flex-wrap gap-1">
          {types.map(t => (
            <button
              key={t}
              onClick={() => setFilter(t)}
              className={`text-xs px-2 py-0.5 rounded border transition-colors ${
                filter === t
                  ? 'bg-blue-700 text-white border-blue-700'
                  : 'bg-gray-50 text-gray-600 border-gray-300 hover:bg-gray-100'
              }`}
            >
              {t === 'all' ? `All (${evidence.length})` : t.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      </div>
      <div className="grid md:grid-cols-2 gap-3">
        {sorted.map(ev => <EvidenceCard key={ev.id} ev={ev} />)}
      </div>
      {hardContradictions?.length > 0 && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800">
          <div className="font-bold mb-1">Hard Contradiction Detected</div>
          {hardContradictions.join(' | ')}
        </div>
      )}
    </div>
  )
}

function LiveIndicator({ active }) {
  if (!active) return null
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-blue-600 font-medium animate-pulse">
      <span className="w-2 h-2 rounded-full bg-blue-500 inline-block animate-ping" />
      Agent running…
    </span>
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
  const pollingRef = useRef(null)
  const auditEndRef = useRef(null)

  // Fetch everything — returns true if investigation is still in progress
  const load = async (silent = false) => {
    if (!silent) setLoading(true)
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

      const status = d.status === 'fulfilled' ? d.value?.status : null
      const stillInvestigating = status === 'investigating' && dec.status === 'fulfilled' && !dec.value
      return stillInvestigating
    } finally {
      if (!silent) setLoading(false)
    }
  }

  // Poll every 2.5 s while agent is active; stop once decision lands
  const startPolling = () => {
    if (pollingRef.current) return
    pollingRef.current = setInterval(async () => {
      const stillRunning = await load(true)
      if (!stillRunning) stopPolling()
      // Scroll new audit entries into view
      auditEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }, 2500)
  }

  const stopPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }

  useEffect(() => {
    load().then(stillRunning => {
      if (stillRunning) { setInvestigating(true); startPolling() }
    })
    return stopPolling
  }, [disputeId])

  const handleInvestigate = () => {
    setInvestigating(true)
    // Try WebSocket streaming; fall back to REST polling
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const wsUrl = `${proto}://${window.location.host}/ws/disputes/${disputeId}/stream`
    let ws
    try {
      ws = new WebSocket(wsUrl)
      ws.onmessage = (ev) => {
        const msg = JSON.parse(ev.data)
        if (msg.type === 'audit') {
          setAudit(prev => {
            if (prev.find(e => e.id === msg.entry.id)) return prev
            return [...prev, msg.entry]
          })
          auditEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
        } else if (msg.type === 'done' || msg.type === 'error') {
          ws.close()
          stopPolling()
          load().then(() => setInvestigating(false))
        }
      }
      ws.onerror = () => {
        // WS unavailable — fall back to REST polling
        ws = null
        startPolling()
        fetch(`/api/disputes/${disputeId}/investigate`, { method: 'POST' })
          .then(() => { stopPolling(); load().then(() => setInvestigating(false)) })
      }
    } catch {
      startPolling()
      fetch(`/api/disputes/${disputeId}/investigate`, { method: 'POST' })
        .then(() => { stopPolling(); load().then(() => setInvestigating(false)) })
    }
  }

  if (loading) return <div className="text-gray-500 text-center py-12">Loading case…</div>
  if (!dispute) return <div className="text-red-500 text-center py-12">Dispute not found</div>

  return (
    <div>
      {/* Breadcrumb */}
      <div className="mb-4 text-sm text-gray-500 flex items-center gap-1">
        <Link to="/dashboard" className="hover:text-blue-600">Dashboard</Link>
        <span className="mx-1">›</span>
        <span className="text-gray-800 font-medium font-mono">{disputeId.slice(0, 8)}</span>
        <CopyButton text={disputeId} label="dispute ID" />
      </div>

      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">{dispute.order_id}</h1>
            <p className="text-gray-500 text-sm mt-0.5 capitalize">
              {dispute.dispute_type.replace(/_/g, ' ')} · {dispute.status}
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <LiveIndicator active={investigating} />
            {decision && <GateBadge gate={decision.gate_result} />}
            {!decision && !investigating && (dispute.status === 'open' || dispute.status === 'failed') && (
              <button
                onClick={handleInvestigate}
                className="bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-800"
              >
                {dispute.status === 'failed' ? '↺ Retry Autopilot' : '⚡ Run Autopilot'}
              </button>
            )}
            {decision && (
              <a
                href={`/api/cases/${disputeId}/export`}
                download
                className="text-xs text-gray-400 hover:text-gray-600 underline"
              >
                ↓ Export JSON
              </a>
            )}
            {dispute.status === 'failed' && !investigating && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-red-100 text-red-700 border border-red-300 text-sm font-medium">
                ✕ Investigation failed — retry above
              </span>
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
            <p className="text-sm text-gray-700">
              {dispute.seller_narrative || <em className="text-gray-400">No response yet</em>}
            </p>
            {!decision && (dispute.status === 'open' || dispute.status === 'investigating') && (
              <SellerReplyForm
                disputeId={disputeId}
                currentNarrative={dispute.seller_narrative}
                onSaved={() => load()}
              />
            )}
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
          <ConfidenceBreakdown
            verdict={decision.verdict}
            stabilityResult={decision.stability_result}
          />
          {decision.abstention_reason && (
            <div className="mt-4 bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800">
              <div className="font-bold mb-1">Why NON LIQUET</div>
              {decision.abstention_reason}
            </div>
          )}
        </div>
      )}

      {/* Innovative feature panels */}
      {decision && (
        <>
          <GhostCasesPanel ghostResult={decision.ghost_case_result} />
          <StabilityGauge stabilityResult={decision.stability_result} />
          <SkepticPanel skepticResult={decision.skeptic_result} />
        </>
      )}

      {/* Evidence */}
      {caseFile && caseFile.evidence?.length > 0 && (
        <EvidenceSection evidence={caseFile.evidence} hardContradictions={caseFile.hard_contradictions} />
      )}

      {/* Audit trail — live-updating while agent runs */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-bold text-gray-900">
            Audit Trail {audit.length > 0 && <span className="text-gray-400 font-normal text-sm">({audit.length} events)</span>}
          </h2>
          <LiveIndicator active={investigating} />
        </div>
        <div className="max-h-[500px] overflow-y-auto pr-1">
          <AuditTimeline audit={audit} investigating={investigating} />
          <div ref={auditEndRef} />
        </div>
      </div>
    </div>
  )
}
