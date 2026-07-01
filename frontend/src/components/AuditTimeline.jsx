import React from 'react'

const EVENT_ICONS = {
  investigation_started: '🚀',
  case_assembled: '📂',
  ghost_cases_injected: '👻',
  claims_extracted: '📝',
  stability_scored: '🎲',
  verdict_produced: '⚖️',
  skeptic_complete: '🔥',
  auto_resolved: '✅',
  escalated_to_human: '👤',
  investigation_failed: '❌',
}

const EVENT_COLORS = {
  investigation_started: 'border-blue-300 bg-blue-50',
  case_assembled: 'border-indigo-300 bg-indigo-50',
  ghost_cases_injected: 'border-purple-300 bg-purple-50',
  claims_extracted: 'border-cyan-300 bg-cyan-50',
  stability_scored: 'border-yellow-300 bg-yellow-50',
  verdict_produced: 'border-green-300 bg-green-50',
  skeptic_complete: 'border-rose-300 bg-rose-50',
  auto_resolved: 'border-emerald-300 bg-emerald-50',
  escalated_to_human: 'border-amber-300 bg-amber-50',
}

function formatData(data) {
  if (!data || Object.keys(data).length === 0) return null
  return Object.entries(data)
    .filter(([k]) => !['actor', 'event'].includes(k))
    .map(([k, v]) => `${k}: ${typeof v === 'object' ? JSON.stringify(v) : v}`)
    .join(' · ')
}

export default function AuditTimeline({ audit, investigating }) {
  if (!audit || audit.length === 0) {
    if (!investigating) return (
      <p className="text-gray-400 text-sm">No audit events yet. Run the autopilot to see agent steps here.</p>
    )
    return (
      <div className="space-y-2">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-10 bg-gray-100 rounded-lg animate-pulse" />
        ))}
      </div>
    )
  }

  return (
    <div className="relative">
      <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gray-200" />
      <div className="space-y-3">
        {audit.map((e, idx) => {
          const icon = EVENT_ICONS[e.event] || '•'
          const colorClass = EVENT_COLORS[e.event] || 'border-gray-200 bg-gray-50'
          const dataStr = formatData(e.data)
          return (
            <div key={e.id} className="relative flex gap-3 items-start">
              <div className={`relative z-10 w-10 h-10 rounded-full border-2 flex items-center justify-center text-base shrink-0 ${colorClass}`}>
                {icon}
              </div>
              <div className="flex-1 min-w-0 pt-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-medium text-gray-800 text-sm">{e.event.replace(/_/g, ' ')}</span>
                  <span className="text-gray-400 text-xs">
                    {new Date(e.timestamp).toLocaleTimeString()}
                  </span>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                    e.actor === 'agent' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'
                  }`}>
                    {e.actor}
                  </span>
                </div>
                {dataStr && (
                  <div className="text-gray-500 text-xs mt-0.5 truncate">{dataStr}</div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
