import React, { useEffect, useState } from 'react'

function StatusDot({ ok }) {
  return (
    <span className={`inline-block w-2.5 h-2.5 rounded-full mr-2 ${ok ? 'bg-green-500' : 'bg-gray-300'}`} />
  )
}

function Section({ title, icon, children }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
      <h2 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
        <span className="text-xl">{icon}</span>{title}
      </h2>
      {children}
    </div>
  )
}

function Row({ label, value, mono }) {
  return (
    <div className="flex items-start justify-between py-2 border-b border-gray-100 last:border-0">
      <span className="text-sm text-gray-500 w-48 shrink-0">{label}</span>
      <span className={`text-sm text-gray-800 text-right ${mono ? 'font-mono' : ''}`}>{value}</span>
    </div>
  )
}

export default function Automation() {
  const [emailStatus, setEmailStatus] = useState(null)
  const [polling, setPolling] = useState(false)
  const [pollResult, setPollResult] = useState(null)

  const load = () =>
    fetch('/api/email/status').then(r => r.json()).then(setEmailStatus).catch(() => {})

  useEffect(() => { load() }, [])

  const triggerPoll = async () => {
    setPolling(true)
    setPollResult(null)
    try {
      const r = await fetch('/api/email/poll', { method: 'POST' })
      const d = await r.json()
      setPollResult(d)
      load()
    } finally {
      setPolling(false)
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Automation Flows</h1>
        <p className="text-gray-500 text-sm mt-1">
          End-to-end workflow: email in → agent investigates → webhook executes → email out
        </p>
      </div>

      {/* Flow diagram */}
      <div className="bg-gradient-to-r from-blue-50 to-emerald-50 border border-blue-200 rounded-xl p-5 mb-6">
        <div className="flex flex-wrap items-center gap-2 text-sm font-medium">
          {[
            { icon: '📧', label: 'Buyer emails complaint' },
            { icon: '→', label: null },
            { icon: '🤖', label: 'Agent parses & investigates' },
            { icon: '→', label: null },
            { icon: '⚖️', label: 'LIQUET gate' },
            { icon: '→', label: null },
            { icon: '✅', label: 'Webhook fires', sub: 'or' },
            { icon: '👤', label: 'Reviewer approves' },
            { icon: '→', label: null },
            { icon: '📧', label: 'Both parties notified' },
          ].map((step, i) =>
            step.label ? (
              <div key={i} className="flex items-center gap-1 bg-white border border-blue-200 rounded-lg px-3 py-2">
                <span>{step.icon}</span>
                <span className="text-gray-700">{step.label}</span>
                {step.sub && <span className="text-xs text-gray-400 ml-1">({step.sub})</span>}
              </div>
            ) : (
              <span key={i} className="text-blue-400 font-bold">{step.icon}</span>
            )
          )}
        </div>
      </div>

      {/* Feature 1 — Email Intake */}
      <Section title="Email-Driven Dispute Intake" icon="📧">
        <p className="text-sm text-gray-500 mb-4">
          The agent polls an IMAP inbox. When a complaint email arrives, it uses
          <span className="font-mono text-xs bg-gray-100 px-1 rounded ml-1">qwen3.7-max</span> to
          extract the order ID, dispute type, and narrative — then creates a dispute and starts
          investigation automatically, replying to the sender with a case reference.
        </p>
        {emailStatus ? (
          <>
            <Row label="Polling active"
              value={<><StatusDot ok={emailStatus.enabled} />{emailStatus.enabled ? 'Yes' : 'No (set EMAIL_POLLING_ENABLED=true)'}</>} />
            <Row label="IMAP host" value={emailStatus.imap_host} mono />
            <Row label="Inbox account" value={emailStatus.imap_user} mono />
            <Row label="Poll interval" value={`${emailStatus.poll_interval_seconds}s`} />
            <Row label="Last poll" value={emailStatus.last_poll_at
              ? new Date(emailStatus.last_poll_at * 1000).toLocaleTimeString()
              : 'Never'} />
            <Row label="Total processed" value={emailStatus.total_processed} />
          </>
        ) : (
          <div className="text-sm text-gray-400">Loading…</div>
        )}
        <div className="mt-4 flex items-center gap-3">
          <button
            onClick={triggerPoll}
            disabled={polling}
            className="bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-blue-800 disabled:opacity-50 transition-colors"
          >
            {polling ? '⟳ Checking inbox…' : '📬 Check Inbox Now'}
          </button>
          {pollResult && (
            <span className={`text-sm ${pollResult.processed > 0 ? 'text-green-600 font-medium' : 'text-gray-500'}`}>
              {pollResult.message}
            </span>
          )}
        </div>
        <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs text-blue-700">
          <strong>How to test:</strong> Send an email to <code>{emailStatus?.imap_user || 'your-configured-inbox'}</code> with
          subject "Order ORD-1234 complaint" and describe a dispute in the body.
          The agent will reply with a case reference within the poll interval.
        </div>
      </Section>

      {/* Feature 2 — Webhooks */}
      <Section title="Resolution Execution via Webhook" icon="🔗">
        <p className="text-sm text-gray-500 mb-4">
          When the LIQUET gate passes, the agent POSTs to your order system's webhook with the
          resolution action (<code className="text-xs bg-gray-100 px-1 rounded">full_refund</code>,{' '}
          <code className="text-xs bg-gray-100 px-1 rounded">deny_claim</code>, etc.) and emails
          both parties. NON LIQUET fires a separate escalation webhook with the review URL.
        </p>
        {emailStatus && (
          <>
            <Row label="Resolution webhook"
              value={<><StatusDot ok={emailStatus.resolution_webhook} />
                {emailStatus.resolution_webhook ? 'Configured' : 'Not set (RESOLUTION_WEBHOOK_URL)'}</>} />
            <Row label="Escalation webhook"
              value={<><StatusDot ok={emailStatus.escalation_webhook} />
                {emailStatus.escalation_webhook ? 'Configured' : 'Not set (ESCALATION_WEBHOOK_URL)'}</>} />
          </>
        )}
        <div className="mt-4 bg-gray-50 border border-gray-200 rounded-lg p-3 text-xs font-mono text-gray-700 overflow-x-auto">
          <div className="text-gray-400 mb-1">// Example LIQUET webhook payload</div>
          {JSON.stringify({
            event: "dispute.resolved",
            dispute_id: "a272b8b9...",
            order_id: "ORD-004",
            resolution: "full_refund",
            confidence: 0.923,
            amount: 649.00,
            rationale: "Carrier scan confirms delivery but vision evidence shows pre-existing damage.",
            gate: "LIQUET",
          }, null, 2)}
        </div>
      </Section>

      {/* Feature 3 — Human Approval */}
      <Section title="Human-in-the-Loop Approval" icon="👤">
        <p className="text-sm text-gray-500 mb-4">
          When NON LIQUET fires, the reviewer receives an email with the full case brief and
          three one-click buttons — <strong>Approve Agent Verdict</strong>, <strong>Override → Deny</strong>,
          or <strong>Override → Full Refund</strong>. Clicking any button validates a signed
          72-hour token, executes the resolution, fires the webhook, and notifies both parties.
          No login required.
        </p>
        {emailStatus && (
          <Row label="Reviewer email"
            value={<><StatusDot ok={!!emailStatus.reviewer_email && emailStatus.reviewer_email !== '(not configured)'} />
              {emailStatus.reviewer_email}</>} />
        )}
        <div className="mt-4 bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-800">
          <strong>How it works:</strong> Run autopilot on a dispute where confidence is below 80% or
          value exceeds $500. The reviewer email will receive an approval link immediately after escalation.
          The approval page is served at{' '}
          <code className="bg-amber-100 px-1 rounded">/api/cases/&#123;id&#125;/approve?token=...</code>
        </div>
        <div className="mt-3 text-xs text-gray-400">
          Tokens are HMAC-SHA256 signed with <code>APPROVAL_SECRET</code> and expire after 72 hours.
        </div>
      </Section>
    </div>
  )
}
