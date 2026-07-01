import React from 'react'

function RunDot({ run, isWinner }) {
  const color = run.resolution === 'full_refund' ? 'bg-blue-400' :
    run.resolution === 'partial_refund' ? 'bg-yellow-400' :
    run.resolution === 'replacement' ? 'bg-purple-400' :
    run.resolution === 'deny' ? 'bg-red-400' :
    run.resolution === 'escalate' ? 'bg-gray-400' :
    'bg-green-400'

  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-xs ${
      isWinner ? 'bg-white border-gray-300 shadow-sm' : 'bg-gray-50 border-gray-100'
    }`}>
      <span className={`w-2.5 h-2.5 rounded-full ${color} shrink-0`} />
      <div>
        <div className="font-medium text-gray-700 capitalize">
          {run.resolution.replace(/_/g, ' ')}
        </div>
        <div className="text-gray-400">{Math.round(run.confidence * 100)}% conf</div>
      </div>
    </div>
  )
}

export default function StabilityGauge({ stabilityResult }) {
  if (!stabilityResult) return null

  const { runs, stability_score, effective_confidence, is_stable, verdict_distribution } = stabilityResult

  const pct = Math.round(stability_score * 100)
  const effConf = Math.round(effective_confidence * 100)

  const gaugeColor = stability_score >= 1.0 ? 'stroke-green-500' :
    stability_score >= 0.67 ? 'stroke-yellow-500' : 'stroke-red-500'
  const bgColor = stability_score >= 1.0 ? 'bg-green-50 border-green-200' :
    stability_score >= 0.67 ? 'bg-yellow-50 border-yellow-200' : 'bg-red-50 border-red-200'
  const textColor = stability_score >= 1.0 ? 'text-green-700' :
    stability_score >= 0.67 ? 'text-yellow-700' : 'text-red-700'

  const dominantResolution = Object.entries(verdict_distribution || {})
    .sort((a, b) => b[1] - a[1])[0]?.[0]

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
      <div className="flex items-center gap-3 mb-5">
        <span className="text-2xl">🎲</span>
        <div>
          <h2 className="font-bold text-gray-900">Verdict Stability</h2>
          <p className="text-xs text-gray-400">Adjudicator ran 3× with shuffled evidence</p>
        </div>
        <span className={`ml-auto text-xs font-bold px-2.5 py-1 rounded-md border ${bgColor} ${textColor}`}>
          {is_stable ? 'STABLE' : 'UNSTABLE'}
        </span>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Runs */}
        <div>
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Three independent runs
          </div>
          <div className="space-y-2">
            {(runs || []).map(run => (
              <RunDot
                key={run.run_index}
                run={run}
                isWinner={run.resolution === dominantResolution}
              />
            ))}
          </div>
        </div>

        {/* Scores */}
        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>Stability score</span>
              <span className="font-bold">{pct}%</span>
            </div>
            <div className="bg-gray-100 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-700 ${
                  stability_score >= 1.0 ? 'bg-green-500' :
                  stability_score >= 0.67 ? 'bg-yellow-500' : 'bg-red-400'
                }`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>Effective confidence</span>
              <span className="font-bold">{effConf}%</span>
            </div>
            <div className="bg-gray-100 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-700 ${
                  effConf >= 80 ? 'bg-green-500' : effConf >= 60 ? 'bg-yellow-500' : 'bg-red-400'
                }`}
                style={{ width: `${effConf}%` }}
              />
            </div>
          </div>

          <div className={`rounded-lg border p-3 text-xs ${bgColor} ${textColor}`}>
            {is_stable ? (
              <>
                <span className="font-semibold">All runs agree.</span>{' '}
                The verdict is robust to evidence ordering — confidence is reliable.
              </>
            ) : (
              <>
                <span className="font-semibold">Verdict changed across runs.</span>{' '}
                Evidence order affected the outcome — confidence has been downweighted.
                {stability_score < 0.67 && ' Case forced to NON LIQUET.'}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
