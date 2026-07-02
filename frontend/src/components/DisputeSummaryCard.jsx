import React from 'react'
import { Link } from 'react-router-dom'

const STATUS_PILL = {
  open: 'bg-yellow-100 text-yellow-700',
  investigating: 'bg-blue-100 text-blue-700',
  resolved: 'bg-green-100 text-green-700',
  escalated: 'bg-amber-100 text-amber-700',
  closed: 'bg-gray-100 text-gray-500',
  failed: 'bg-red-100 text-red-700',
}

function relativeAge(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${Math.max(mins, 1)}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

export default function DisputeSummaryCard({ dispute }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 hover:border-blue-300 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <Link
            to={`/cases/${dispute.id}`}
            className="font-semibold text-gray-900 hover:text-blue-700 text-sm truncate block"
          >
            {dispute.order_id}
          </Link>
          <p className="text-xs text-gray-500 mt-0.5 capitalize">
            {dispute.dispute_type.replace(/_/g, ' ')}
          </p>
        </div>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full shrink-0 ${STATUS_PILL[dispute.status] || 'bg-gray-100 text-gray-600'}`}>
          {dispute.status}
        </span>
      </div>
      <p className="text-xs text-gray-500 mt-2 line-clamp-2">{dispute.buyer_narrative}</p>
      <div className="flex items-center justify-between mt-3 pt-2 border-t border-gray-100">
        <span className="text-xs font-mono text-gray-400">{dispute.id.slice(0, 8)}</span>
        <span className="text-xs text-gray-400">{relativeAge(dispute.created_at)}</span>
      </div>
    </div>
  )
}
