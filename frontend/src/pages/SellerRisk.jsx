import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

const RISK_COLOR = {
  HIGH: 'bg-red-100 text-red-800 border-red-200',
  MEDIUM: 'bg-amber-100 text-amber-800 border-amber-200',
  LOW: 'bg-green-100 text-green-800 border-green-200',
}

function PatternBar({ score }) {
  const pct = Math.round(score * 100)
  const color = pct >= 70 ? 'bg-red-400' : pct >= 40 ? 'bg-amber-400' : 'bg-green-400'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-100 rounded-full h-1.5 min-w-[60px]">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-500 w-8 text-right">{pct}%</span>
    </div>
  )
}

export default function SellerRisk() {
  const [sellers, setSellers] = useState([])
  const [loading, setLoading] = useState(true)
  const [riskFilter, setRiskFilter] = useState('')
  const [search, setSearch] = useState('')

  useEffect(() => {
    fetch('/api/seller-risk')
      .then(r => r.json())
      .then(data => { setSellers(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const filtered = sellers
    .filter(s => !riskFilter || s.risk_level === riskFilter)
    .filter(s => !search || s.seller_id.toLowerCase().includes(search.toLowerCase()))
  const highRisk = sellers.filter(s => s.risk_level === 'HIGH').length
  const medRisk = sellers.filter(s => s.risk_level === 'MEDIUM').length

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Seller Risk Intelligence</h1>
        <p className="text-gray-500 text-sm mt-1">
          Sellers ranked by dispute volume and pattern concentration — powered by Ghost Cases
        </p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
          <div className="text-3xl font-bold text-gray-800">{sellers.length}</div>
          <div className="text-sm text-gray-500">Total sellers</div>
        </div>
        <div className="bg-white rounded-lg border border-red-200 p-4 shadow-sm">
          <div className="text-3xl font-bold text-red-700">{highRisk}</div>
          <div className="text-sm text-gray-500">High risk</div>
        </div>
        <div className="bg-white rounded-lg border border-amber-200 p-4 shadow-sm">
          <div className="text-3xl font-bold text-amber-700">{medRisk}</div>
          <div className="text-sm text-gray-500">Medium risk</div>
        </div>
      </div>

      {/* Search + Filter */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <input
          type="text"
          placeholder="Search by seller ID…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="flex-1 border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <div className="flex gap-2 mb-4">
        {['', 'HIGH', 'MEDIUM', 'LOW'].map(r => (
          <button
            key={r}
            onClick={() => setRiskFilter(r)}
            className={`px-3 py-1 rounded-full text-sm font-medium border transition-colors ${
              riskFilter === r
                ? 'bg-blue-700 text-white border-blue-700'
                : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
            }`}
          >
            {r || 'All'}
          </button>
        ))}
      </div>

      {loading && <div className="text-gray-400 text-center py-12">Loading seller data…</div>}

      {!loading && filtered.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          No sellers with dispute history yet.{' '}
          <Link to="/new" className="text-blue-600 underline">Submit a dispute</Link> to generate data.
        </div>
      )}

      {!loading && filtered.length > 0 && (
        <div className="space-y-3">
          {filtered.map(seller => (
            <div
              key={seller.seller_id}
              className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="font-mono font-bold text-gray-800">{seller.seller_id}</div>
                  <div className="text-xs text-gray-400 mt-0.5">
                    {seller.total_disputes} dispute{seller.total_disputes !== 1 ? 's' : ''} ·
                    {(seller.platform_share * 100).toFixed(1)}% of platform
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <span className={`text-xs font-bold px-2.5 py-1 rounded-md border ${RISK_COLOR[seller.risk_level]}`}>
                    {seller.risk_level} RISK
                  </span>
                  <Link
                    to={`/dashboard?seller_id=${seller.seller_id}`}
                    className="text-xs text-blue-600 hover:underline"
                  >
                    View cases →
                  </Link>
                </div>
              </div>

              <div className="grid sm:grid-cols-3 gap-4">
                <div>
                  <div className="text-xs text-gray-500 mb-1">Pattern concentration</div>
                  <PatternBar score={seller.pattern_score} />
                  <div className="text-xs text-gray-400 mt-0.5 capitalize">
                    dominant: {seller.dominant_type.replace(/_/g, ' ')}
                  </div>
                </div>

                <div>
                  <div className="text-xs text-gray-500 mb-2">Resolution outcomes</div>
                  <div className="flex gap-2 text-xs">
                    <span className="bg-green-50 text-green-700 px-2 py-0.5 rounded border border-green-200">
                      {seller.resolved} resolved
                    </span>
                    <span className="bg-amber-50 text-amber-700 px-2 py-0.5 rounded border border-amber-200">
                      {seller.escalated} escalated
                    </span>
                  </div>
                </div>

                <div>
                  <div className="text-xs text-gray-500 mb-2">Type breakdown</div>
                  <div className="flex flex-wrap gap-1">
                    {Object.entries(seller.type_breakdown).map(([type, count]) => (
                      <span key={type} className="bg-gray-100 text-gray-600 text-xs px-1.5 py-0.5 rounded">
                        {type.replace(/_/g, ' ')}: {count}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
