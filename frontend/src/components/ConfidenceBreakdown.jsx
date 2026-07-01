import React from 'react'

function Bar({ value, label, color, dim = false }) {
  const pct = Math.round(value * 100)
  const barColor = dim ? 'bg-gray-300' : color
  return (
    <div className={dim ? 'opacity-50' : ''}>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-500">{label}</span>
        <span className={`font-bold ${dim ? 'text-gray-400' : 'text-gray-700'}`}>{pct}%</span>
      </div>
      <div className="bg-gray-100 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-700 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

export default function ConfidenceBreakdown({ verdict, stabilityResult }) {
  if (!verdict) return null

  const rawConf = verdict.confidence
  const hasStability = stabilityResult && stabilityResult.stability_score < 1.0
  const effectiveConf = stabilityResult ? stabilityResult.effective_confidence : rawConf
  const stabilityScore = stabilityResult?.stability_score ?? 1.0

  const rawPct = Math.round(rawConf * 100)
  const effPct = Math.round(effectiveConf * 100)
  const delta = rawPct - effPct

  const rawColor = rawConf >= 0.8 ? 'bg-green-400' : rawConf >= 0.6 ? 'bg-yellow-400' : 'bg-red-400'
  const effColor = effectiveConf >= 0.8 ? 'bg-green-500' : effectiveConf >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'

  return (
    <div className="bg-gray-50 rounded-lg border border-gray-200 p-4 mt-4">
      <div className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-3">
        Confidence Breakdown
      </div>
      <div className="space-y-3">
        <Bar value={rawConf} label="Raw adjudicator confidence" color={rawColor} dim={hasStability} />
        {hasStability && (
          <>
            <Bar
              value={stabilityScore}
              label={`Stability factor (${Math.round(stabilityScore * 100)}% agreement across runs)`}
              color="bg-blue-400"
            />
            <div className="border-t border-gray-200 pt-2">
              <Bar
                value={effectiveConf}
                label={`Effective confidence (raw × stability)`}
                color={effColor}
              />
              {delta > 0 && (
                <div className="text-xs text-amber-600 mt-1">
                  ↓ {delta}pp reduction from variance penalty
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
