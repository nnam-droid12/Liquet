import React, { useEffect, useState } from 'react'
import DigestWidget from './DigestWidget.jsx'

function MetricCard({ label, value, sub, color = 'text-gray-800' }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <div className={`text-4xl font-black mb-1 ${color}`}>{value}</div>
      <div className="text-sm font-medium text-gray-600">{label}</div>
      {sub && <div className="text-xs text-gray-400 mt-0.5">{sub}</div>}
    </div>
  )
}

function HorizontalBar({ label, value, max, color = 'bg-blue-500' }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0
  return (
    <div className="flex items-center gap-3">
      <div className="w-36 text-xs text-gray-600 capitalize truncate">{label.replace(/_/g, ' ')}</div>
      <div className="flex-1 bg-gray-100 rounded-full h-2">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <div className="text-xs font-bold text-gray-700 w-8 text-right">{value}</div>
    </div>
  )
}

function MCPStatusRow({ name, data }) {
  const isOk = data?.status === 'ok'
  return (
    <div className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs ${
      isOk ? 'bg-green-50 border border-green-100' : 'bg-red-50 border border-red-100'
    }`}>
      <span className={`font-mono font-medium ${isOk ? 'text-green-700' : 'text-red-700'}`}>
        {name}
      </span>
      <div className="flex items-center gap-3">
        {isOk && (
          <span className="text-green-600">{data.tool_count} tools</span>
        )}
        <span className={`w-2 h-2 rounded-full ${isOk ? 'bg-green-500' : 'bg-red-500'}`} />
      </div>
    </div>
  )
}

function DailyBarChart({ data, label }) {
  if (!data || data.length === 0) return null
  const max = Math.max(...data.map(d => d.count), 1)
  const H = 60, W = 400
  const barW = Math.max(2, Math.floor(W / data.length) - 1)

  return (
    <div>
      <div className="text-xs font-medium text-gray-500 mb-2">{label}</div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-16">
        {data.map((d, i) => {
          const h = Math.max(2, Math.round((d.count / max) * (H - 4)))
          return (
            <rect
              key={d.date}
              x={i * (barW + 1)}
              y={H - h}
              width={barW}
              height={h}
              fill="#3b82f6"
              opacity={0.7}
            >
              <title>{d.date}: {d.count}</title>
            </rect>
          )
        })}
      </svg>
      <div className="flex justify-between text-[10px] text-gray-400 mt-0.5">
        <span>{data[0]?.date}</span>
        <span>{data[data.length - 1]?.date}</span>
      </div>
    </div>
  )
}

function ConfidenceHistogram({ data }) {
  if (!data || data.histogram.length === 0) return null
  const max = Math.max(...data.histogram.map(b => b.count), 1)
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm mb-6">
      <div className="font-bold text-gray-900 mb-1">Confidence Distribution</div>
      <div className="text-xs text-gray-400 mb-4">
        {data.total} verdicts · min {Math.round(data.min * 100)}% · max {Math.round(data.max * 100)}% · mean {Math.round(data.mean * 100)}%
      </div>
      <div className="flex items-end gap-1 h-24">
        {data.histogram.map((b, i) => {
          const pct = Math.round((b.count / max) * 100)
          const isHigh = i >= data.histogram.length * 0.8
          return (
            <div key={b.range} className="flex-1 flex flex-col items-center gap-1">
              <div
                className={`w-full rounded-t transition-all ${isHigh ? 'bg-emerald-500' : 'bg-blue-400'}`}
                style={{ height: `${Math.max(pct, b.count > 0 ? 4 : 0)}%` }}
                title={`${b.range}: ${b.count}`}
              />
            </div>
          )
        })}
      </div>
      <div className="flex justify-between text-[10px] text-gray-400 mt-1">
        <span>0%</span>
        <span>50%</span>
        <span>100%</span>
      </div>
    </div>
  )
}

export default function Analytics() {
  const [stats, setStats] = useState(null)
  const [mcpStatus, setMcpStatus] = useState(null)
  const [sellerRisk, setSellerRisk] = useState([])
  const [dailyMetrics, setDailyMetrics] = useState(null)
  const [confHistogram, setConfHistogram] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch('/api/stats').then(r => r.ok ? r.json() : null),
      fetch('/api/mcp-status').then(r => r.ok ? r.json() : null),
      fetch('/api/seller-risk').then(r => r.ok ? r.json() : []),
      fetch('/api/metrics/daily?days=30').then(r => r.ok ? r.json() : null),
      fetch('/api/stats/confidence-histogram?buckets=10').then(r => r.ok ? r.json() : null),
    ]).then(([statsData, mcpData, riskData, daily, histogram]) => {
      setStats(statsData)
      setMcpStatus(mcpData)
      setSellerRisk(riskData || [])
      setDailyMetrics(daily)
      setConfHistogram(histogram)
      setLoading(false)
    })
  }, [])

  const [refreshed, setRefreshed] = useState(null)

  if (loading) return <div className="text-gray-400 text-center py-12">Loading analytics…</div>

  const autoRate = stats ? Math.round(stats.auto_resolution_rate * 100) : 0
  const avgConf = stats ? Math.round(stats.avg_confidence * 100) : 0
  const typeEntries = stats ? Object.entries(stats.dispute_type_breakdown || {}).sort((a, b) => b[1] - a[1]) : []
  const maxTypeCount = typeEntries.length > 0 ? Math.max(...typeEntries.map(e => e[1])) : 1
  const highRisk = sellerRisk.filter(s => s.risk_level === 'HIGH').length

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Platform Analytics</h1>
          <p className="text-gray-500 text-sm mt-1">
            Live metrics from the Liquet adjudication engine
          </p>
        </div>
        <button
          onClick={() => {
            setLoading(true)
            Promise.all([
              fetch('/api/stats').then(r => r.ok ? r.json() : null),
              fetch('/api/mcp-status').then(r => r.ok ? r.json() : null),
              fetch('/api/seller-risk').then(r => r.ok ? r.json() : []),
              fetch('/api/metrics/daily?days=30').then(r => r.ok ? r.json() : null),
              fetch('/api/stats/confidence-histogram?buckets=10').then(r => r.ok ? r.json() : null),
            ]).then(([s, m, r, d, h]) => {
              setStats(s); setMcpStatus(m); setSellerRisk(r || [])
              setDailyMetrics(d); setConfHistogram(h)
              setLoading(false); setRefreshed(new Date().toLocaleTimeString())
            })
          }}
          className="text-xs text-gray-500 hover:text-gray-800 border border-gray-300 px-3 py-1.5 rounded hover:bg-gray-50 transition-colors"
        >
          ↺ Refresh
        </button>
      </div>
      {refreshed && <p className="text-xs text-gray-400 mb-4">Last refreshed at {refreshed}</p>}

      {/* Key metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <MetricCard label="Disputes processed" value={stats?.total_disputes || 0} color="text-gray-800" />
        <MetricCard label="Auto-resolution rate" value={`${autoRate}%`} sub="LIQUET gate" color="text-emerald-600" />
        <MetricCard label="Avg confidence" value={`${avgConf}%`} sub="across all verdicts" color="text-blue-600" />
        <MetricCard label="High-risk sellers" value={highRisk} sub="recurring pattern ≥70%" color="text-red-600" />
      </div>

      {/* 24h digest */}
      <div className="mb-6">
        <DigestWidget />
      </div>

      {/* Confidence histogram */}
      {confHistogram?.total > 0 && <ConfidenceHistogram data={confHistogram} />}

      {/* Daily submissions chart */}
      {dailyMetrics?.submissions?.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm mb-6">
          <div className="font-bold text-gray-900 mb-4">Daily Dispute Volume (last 30 days)</div>
          <DailyBarChart data={dailyMetrics.submissions} label="Disputes submitted per day" />
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-6 mb-6">
        {/* Gate distribution */}
        {stats?.gate_counts && (
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <div className="font-bold text-gray-900 mb-4">Gate Decision Distribution</div>
            <div className="space-y-3">
              {Object.entries(stats.gate_counts).map(([gate, count]) => (
                <HorizontalBar
                  key={gate}
                  label={gate.replace('_', ' ')}
                  value={count}
                  max={stats.total_disputes}
                  color={gate === 'LIQUET' ? 'bg-emerald-500' : 'bg-amber-400'}
                />
              ))}
            </div>
            <div className="mt-3 text-xs text-gray-400">
              LIQUET = auto-resolved · NON_LIQUET = escalated to human
            </div>
          </div>
        )}

        {/* Dispute type breakdown */}
        {typeEntries.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <div className="font-bold text-gray-900 mb-4">Dispute Types</div>
            <div className="space-y-3">
              {typeEntries.map(([type, count]) => (
                <HorizontalBar
                  key={type}
                  label={type}
                  value={count}
                  max={maxTypeCount}
                  color="bg-blue-500"
                />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* MCP server status */}
      {mcpStatus && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="font-bold text-gray-900">MCP Tool Servers</div>
            <span className={`text-xs font-bold px-2 py-1 rounded ${
              mcpStatus.all_healthy ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}>
              {mcpStatus.healthy}/{mcpStatus.total} healthy
            </span>
          </div>
          <div className="grid sm:grid-cols-2 gap-2">
            {Object.entries(mcpStatus.servers || {}).map(([name, data]) => (
              <MCPStatusRow key={name} name={name} data={data} />
            ))}
          </div>
        </div>
      )}

      {/* Seller risk table */}
      {sellerRisk.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <div className="font-bold text-gray-900 mb-4">Seller Risk Summary</div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left pb-2 text-xs font-medium text-gray-500">Seller</th>
                  <th className="text-left pb-2 text-xs font-medium text-gray-500">Disputes</th>
                  <th className="text-left pb-2 text-xs font-medium text-gray-500">Pattern</th>
                  <th className="text-left pb-2 text-xs font-medium text-gray-500">Risk</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {sellerRisk.slice(0, 5).map(s => (
                  <tr key={s.seller_id}>
                    <td className="py-2 font-mono text-xs text-gray-600">{s.seller_id}</td>
                    <td className="py-2 text-gray-700">{s.total_disputes}</td>
                    <td className="py-2 text-gray-600">{Math.round(s.pattern_score * 100)}%</td>
                    <td className="py-2">
                      <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${
                        s.risk_level === 'HIGH' ? 'bg-red-100 text-red-700' :
                        s.risk_level === 'MEDIUM' ? 'bg-amber-100 text-amber-700' :
                        'bg-green-100 text-green-700'
                      }`}>
                        {s.risk_level}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
