import React from 'react'

export function SkeletonLine({ className = '' }) {
  return <div className={`bg-gray-200 rounded animate-pulse ${className}`} />
}

export function SkeletonCard({ className = '' }) {
  return (
    <div className={`bg-white rounded-xl border border-gray-200 p-5 space-y-3 ${className}`}>
      <SkeletonLine className="h-4 w-2/3" />
      <SkeletonLine className="h-3 w-full" />
      <SkeletonLine className="h-3 w-4/5" />
    </div>
  )
}

export function SkeletonStatGrid({ count = 6 }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="bg-white rounded-lg border border-gray-200 p-4 space-y-2">
          <SkeletonLine className="h-8 w-16" />
          <SkeletonLine className="h-3 w-20" />
        </div>
      ))}
    </div>
  )
}

export function SkeletonTableRows({ rows = 5 }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="bg-gray-50 h-10 border-b border-gray-200" />
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 px-4 py-3 border-b border-gray-100">
          <SkeletonLine className="h-3 w-16" />
          <SkeletonLine className="h-3 w-24" />
          <SkeletonLine className="h-3 w-20" />
          <SkeletonLine className="h-5 w-16 rounded-full" />
          <SkeletonLine className="h-3 w-12 ml-auto" />
        </div>
      ))}
    </div>
  )
}
