import React from 'react'

const STATUS_STYLES = {
  open: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  investigating: 'bg-blue-100 text-blue-800 border-blue-200 animate-pulse',
  resolved: 'bg-green-100 text-green-800 border-green-200',
  escalated: 'bg-amber-100 text-amber-800 border-amber-200',
  closed: 'bg-gray-100 text-gray-500 border-gray-200',
  failed: 'bg-red-100 text-red-800 border-red-200',
}

const STATUS_DOT = {
  open: 'bg-yellow-400',
  investigating: 'bg-blue-400',
  resolved: 'bg-green-500',
  escalated: 'bg-amber-500',
  closed: 'bg-gray-400',
  failed: 'bg-red-500',
}

export default function StatusBadge({ status, showDot = true, className = '' }) {
  const style = STATUS_STYLES[status] || 'bg-gray-100 text-gray-600 border-gray-200'
  const dot = STATUS_DOT[status] || 'bg-gray-400'
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border ${style} ${className}`}>
      {showDot && <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${dot}`} />}
      {status}
    </span>
  )
}
