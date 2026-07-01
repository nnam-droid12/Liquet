import React from 'react'

function PatternBar({ score }) {
  const pct = Math.round(score * 100)
  const color = pct >= 70 ? 'bg-rose-400' : pct >= 40 ? 'bg-amber-400' : 'bg-blue-400'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-100 rounded-full h-1.5">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-bold text-gray-600 w-10 text-right">{pct}%</span>
    </div>
  )
}

export default function GhostCasesPanel({ ghostResult }) {
  if (!ghostResult) return null

  const { similar_cases_count, seller_dispute_rate, pattern_match_score, dominant_resolution, weight } = ghostResult

  const patternPct = Math.round(pattern_match_score * 100)
  const ratePct = Math.round(seller_dispute_rate * 100)
  const hasPattern = similar_cases_count >= 2

  const signalStrength = patternPct >= 70 ? 'HIGH' : patternPct >= 40 ? 'MEDIUM' : 'LOW'
  const signalColor = patternPct >= 70 ? 'text-rose-600 bg-rose-50 border-rose-200' :
    patternPct >= 40 ? 'text-amber-600 bg-amber-50 border-amber-200' :
    'text-blue-600 bg-blue-50 border-blue-200'

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
      <div className="flex items-center gap-3 mb-5">
        <span className="text-2xl">👻</span>
        <div>
          <h2 className="font-bold text-gray-900">Ghost Cases</h2>
          <p className="text-xs text-gray-400">Cross-dispute pattern analysis for this seller</p>
        </div>
        {hasPattern && (
          <span className={`ml-auto text-xs font-bold px-2.5 py-1 rounded-md border ${signalColor}`}>
            {signalStrength} SIGNAL
          </span>
        )}
      </div>

      {!hasPattern ? (
        <div className="text-sm text-gray-400 italic">
          No significant prior dispute history found for this seller. First-time signal.
        </div>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <div className="text-2xl font-black text-gray-800">{similar_cases_count}</div>
              <div className="text-xs text-gray-500 mt-0.5">similar disputes</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <div className="text-2xl font-black text-gray-800">{patternPct}%</div>
              <div className="text-xs text-gray-500 mt-0.5">pattern match</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <div className="text-2xl font-black text-gray-800">{Math.round(weight * 100)}%</div>
              <div className="text-xs text-gray-500 mt-0.5">evidence weight</div>
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>Pattern match rate (same dispute type)</span>
            </div>
            <PatternBar score={pattern_match_score} />
          </div>

          {dominant_resolution && (
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-500">Historical outcome:</span>
              <span className="font-medium text-gray-700 capitalize">{dominant_resolution.replace(/_/g, ' ')}</span>
            </div>
          )}

          <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-600">
            <span className="font-semibold">Synthetic evidence injected.</span>{' '}
            The adjudicator received historical pattern data as an additional evidence item
            (reliability {Math.round(Math.min(0.75, 0.55 + pattern_match_score * 0.2) * 100)}%).
          </div>
        </div>
      )}
    </div>
  )
}
