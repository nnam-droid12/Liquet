import React from 'react'
import { Link } from 'react-router-dom'

export default function EmptyState({ icon = '📭', title, description, action }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
      <div className="text-5xl mb-3">{icon}</div>
      <div className="text-gray-800 font-semibold text-lg mb-1">{title}</div>
      {description && (
        <p className="text-gray-500 text-sm mb-4 max-w-sm mx-auto">{description}</p>
      )}
      {action && (
        <Link
          to={action.to}
          className="inline-flex items-center gap-1.5 bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-md hover:bg-blue-800 transition-colors"
        >
          {action.label}
        </Link>
      )}
    </div>
  )
}
