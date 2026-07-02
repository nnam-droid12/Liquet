export function confidenceLabel(score) {
  if (score >= 0.90) return { label: 'Very High', color: 'text-emerald-700' }
  if (score >= 0.80) return { label: 'High', color: 'text-green-700' }
  if (score >= 0.65) return { label: 'Moderate', color: 'text-yellow-700' }
  if (score >= 0.50) return { label: 'Low', color: 'text-orange-700' }
  return { label: 'Very Low', color: 'text-red-700' }
}

export const DISPUTE_TYPE_ICON = {
  not_as_described: '📋',
  never_arrived: '📦',
  wrong_item: '🔄',
  damaged: '💥',
  counterfeit: '🎭',
  other: '❓',
}

export const DISPUTE_TYPE_LABEL = {
  not_as_described: 'Not as Described',
  never_arrived: 'Never Arrived',
  wrong_item: 'Wrong Item',
  damaged: 'Arrived Damaged',
  counterfeit: 'Counterfeit',
  other: 'Other',
}

export function formatCurrency(amount) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}

export function relativeAge(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${Math.max(mins, 1)}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}d ago`
  return new Date(dateStr).toLocaleDateString()
}
