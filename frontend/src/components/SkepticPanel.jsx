import React, { useState } from 'react'

export default function SkepticPanel({ skepticResult }) {
  const [expanded, setExpanded] = useState(false)

  if (!skepticResult) return null

  const { devil_argument, rebuttal, rebuttal_strength, verdict_contested, contest_summary } = skepticResult

  const strengthPct = Math.round(rebuttal_strength * 100)
  const strengthColor = rebuttal_strength >= 0.75 ? 'text-green-600' :
    rebuttal_strength >= 0.55 ? 'text-yellow-600' : 'text-red-600'
  const strengthBg = rebuttal_strength >= 0.75 ? 'bg-green-50 border-green-200' :
    rebuttal_strength >= 0.55 ? 'bg-yellow-50 border-yellow-200' : 'bg-red-50 border-red-200'
  const barColor = rebuttal_strength >= 0.75 ? 'bg-green-500' :
    rebuttal_strength >= 0.55 ? 'bg-yellow-500' : 'bg-red-400'

  const isStands = contest_summary?.startsWith('STANDS')

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
      <div className="flex items-center gap-3 mb-5">
        <span className="text-2xl">🔥</span>
        <div>
          <h2 className="font-bold text-gray-900">Skeptic Pass</h2>
          <p className="text-xs text-gray-400">Adversarial devil's-advocate challenge</p>
        </div>
        <span className={`ml-auto text-xs font-bold px-2.5 py-1 rounded-md border ${
          verdict_contested
            ? 'bg-red-50 border-red-200 text-red-700'
            : 'bg-green-50 border-green-200 text-green-700'
        }`}>
          {verdict_contested ? 'CONTESTED' : 'VERDICT STANDS'}
        </span>
      </div>

      {/* Summary */}
      <div className={`rounded-lg border p-3 text-sm mb-4 ${strengthBg} ${strengthColor}`}>
        <span className="font-semibold">
          {isStands ? '✓ Stands: ' : '✕ Contested: '}
        </span>
        {contest_summary?.replace(/^(STANDS|CONTESTED):\s*/, '')}
      </div>

      {/* Rebuttal strength bar */}
      <div className="mb-4">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Rebuttal strength</span>
          <span className={`font-bold ${strengthColor}`}>{strengthPct}%</span>
        </div>
        <div className="bg-gray-100 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-700 ${barColor}`}
            style={{ width: `${strengthPct}%` }}
          />
        </div>
        <div className="flex justify-between text-[10px] text-gray-400 mt-0.5">
          <span>Can't rebut</span>
          <span className="text-center">Threshold 55%</span>
          <span>Fully neutralised</span>
        </div>
      </div>

      {/* Toggle detail */}
      <button
        onClick={() => setExpanded(e => !e)}
        className="text-xs text-blue-600 hover:text-blue-800 font-medium mb-3"
      >
        {expanded ? '▲ Hide dialogue' : '▼ Show challenge dialogue'}
      </button>

      {expanded && (
        <div className="space-y-3">
          <div className="bg-red-50 border border-red-100 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-bold text-red-700 uppercase tracking-wide">
                👿 Devil's Advocate
              </span>
            </div>
            <p className="text-sm text-red-800 leading-relaxed">{devil_argument}</p>
          </div>

          <div className="flex justify-center">
            <div className="text-gray-300 text-lg">↓</div>
          </div>

          <div className="bg-green-50 border border-green-100 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-bold text-green-700 uppercase tracking-wide">
                ⚖️ Adjudicator Rebuttal
              </span>
            </div>
            <p className="text-sm text-green-800 leading-relaxed">{rebuttal}</p>
          </div>
        </div>
      )}
    </div>
  )
}
