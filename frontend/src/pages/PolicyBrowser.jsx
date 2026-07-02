import React, { useEffect, useState } from 'react'

const GROUP_LABELS = {
  T: 'Dispute Type Rules',
  V: 'Value Thresholds',
  Q: 'Quality & Condition',
  A: 'Abstention Rules',
  R: 'Resolution Rules',
}

const GROUP_COLORS = {
  T: 'bg-blue-50 border-blue-200 text-blue-800',
  V: 'bg-amber-50 border-amber-200 text-amber-800',
  Q: 'bg-green-50 border-green-200 text-green-800',
  A: 'bg-red-50 border-red-200 text-red-800',
  R: 'bg-purple-50 border-purple-200 text-purple-800',
}

const CODE_COLORS = {
  T: 'bg-blue-100 text-blue-700',
  V: 'bg-amber-100 text-amber-700',
  Q: 'bg-green-100 text-green-700',
  A: 'bg-red-100 text-red-700',
  R: 'bg-purple-100 text-purple-700',
}

function Highlight({ text, term }) {
  if (!term) return <>{text}</>
  const parts = text.split(new RegExp(`(${term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'))
  return (
    <>
      {parts.map((part, i) =>
        part.toLowerCase() === term.toLowerCase()
          ? <mark key={i} className="bg-yellow-200 text-yellow-900 rounded px-0.5">{part}</mark>
          : part
      )}
    </>
  )
}

export default function PolicyBrowser() {
  const [policy, setPolicy] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeGroup, setActiveGroup] = useState('')
  const [search, setSearch] = useState('')

  useEffect(() => {
    fetch('/api/policy')
      .then(r => r.json())
      .then(data => { setPolicy(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-gray-400 text-center py-12">Loading policy…</div>

  if (!policy || !policy.clauses?.length) {
    return (
      <div className="text-center py-12 text-gray-400">
        Policy file not found. Place policy.md in the data/ directory.
      </div>
    )
  }

  const groups = policy.groups || {}
  const groupKeys = Object.keys(groups).sort()

  const allClauses = policy.clauses.filter(c => {
    if (activeGroup && c.code[0] !== activeGroup) return false
    if (search && !c.code.toLowerCase().includes(search.toLowerCase()) &&
        !c.description.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Policy Browser</h1>
        <p className="text-gray-500 text-sm mt-1">
          {policy.clause_count} policy clauses governing autonomous dispute resolution
        </p>
      </div>

      {/* Group filter */}
      <div className="flex gap-2 flex-wrap mb-4">
        <button
          onClick={() => setActiveGroup('')}
          className={`px-3 py-1 rounded-full text-sm font-medium border transition-colors ${
            !activeGroup ? 'bg-blue-700 text-white border-blue-700' : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
          }`}
        >
          All ({policy.clause_count})
        </button>
        {groupKeys.map(g => (
          <button
            key={g}
            onClick={() => setActiveGroup(activeGroup === g ? '' : g)}
            className={`px-3 py-1 rounded-full text-sm font-medium border transition-colors ${
              activeGroup === g
                ? 'bg-blue-700 text-white border-blue-700'
                : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
            }`}
          >
            {GROUP_LABELS[g] || g} ({groups[g].length})
          </button>
        ))}
      </div>

      {/* Search */}
      <input
        type="text"
        placeholder="Search clauses…"
        value={search}
        onChange={e => setSearch(e.target.value)}
        className="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
      />

      {/* Clauses */}
      <div className="space-y-2">
        {allClauses.map(clause => {
          const prefix = clause.code[0]
          const codeColor = CODE_COLORS[prefix] || 'bg-gray-100 text-gray-600'
          const cardColor = GROUP_COLORS[prefix] || 'bg-gray-50 border-gray-200 text-gray-800'
          return (
            <div
              key={clause.code}
              className={`rounded-lg border p-4 flex items-start gap-3 ${cardColor}`}
            >
              <span className={`font-mono font-bold text-xs px-2 py-1 rounded shrink-0 ${codeColor}`}>
                <Highlight text={clause.code} term={search} />
              </span>
              <span className="text-sm">
                <Highlight text={clause.description} term={search} />
              </span>
            </div>
          )
        })}
        {allClauses.length === 0 && (
          <div className="text-gray-400 text-center py-6">No clauses match your search.</div>
        )}
      </div>

      {/* Raw policy */}
      <details className="mt-8">
        <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
          View raw policy document
        </summary>
        <pre className="mt-3 bg-gray-50 border border-gray-200 rounded-lg p-4 text-xs text-gray-600 overflow-x-auto whitespace-pre-wrap max-h-96 overflow-y-auto">
          {policy.raw}
        </pre>
      </details>
    </div>
  )
}
