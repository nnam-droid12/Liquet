import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const DISPUTE_TYPES = [
  { value: 'not_as_described', label: 'Not as Described' },
  { value: 'never_arrived', label: 'Never Arrived' },
  { value: 'wrong_item', label: 'Wrong Item' },
  { value: 'damaged', label: 'Arrived Damaged' },
  { value: 'counterfeit', label: 'Counterfeit' },
  { value: 'other', label: 'Other' },
]

export default function NewDispute() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    order_id: '',
    dispute_type: 'not_as_described',
    buyer_id: '',
    seller_id: '',
    buyer_narrative: '',
    seller_narrative: '',
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [autoInvestigate, setAutoInvestigate] = useState(true)

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      const r = await fetch('/api/disputes/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      if (!r.ok) throw new Error((await r.json()).detail || 'Failed to create dispute')
      const dispute = await r.json()

      if (autoInvestigate) {
        await fetch(`/api/disputes/${dispute.id}/investigate`, { method: 'POST' })
      }
      navigate(`/cases/${dispute.id}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const loadDemo = () => {
    setForm({
      order_id: 'ORD-004',
      dispute_type: 'not_as_described',
      buyer_id: 'USR-B004',
      seller_id: 'USR-S001',
      buyer_narrative: 'I recorded my unboxing on video. The moment I removed the lens from the box it was visibly scratched on the front element. The scratch was there before I touched it. $649 for a damaged lens — I need a full refund.',
      seller_narrative: 'I have detailed inspection photos taken on the day of shipping. The glass was perfect. I\'ve been selling cameras for 8 years with zero complaints. The buyer must have caused the damage after unboxing.',
    })
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">New Dispute</h1>
          <p className="text-gray-500 text-sm mt-1">Submit a marketplace dispute for Liquet to investigate</p>
        </div>
        <button onClick={loadDemo} className="text-sm text-blue-600 hover:text-blue-800 underline">
          Load demo (50/50 case)
        </button>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-5">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Order ID *</label>
            <input
              type="text" required value={form.order_id}
              onChange={e => set('order_id', e.target.value)}
              placeholder="ORD-001"
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Dispute Type *</label>
            <select
              value={form.dispute_type}
              onChange={e => set('dispute_type', e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {DISPUTE_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Buyer ID *</label>
            <input
              type="text" required value={form.buyer_id}
              onChange={e => set('buyer_id', e.target.value)}
              placeholder="USR-B001"
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Seller ID *</label>
            <input
              type="text" required value={form.seller_id}
              onChange={e => set('seller_id', e.target.value)}
              placeholder="USR-S001"
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Buyer's Account *</label>
          <textarea
            required value={form.buyer_narrative}
            onChange={e => set('buyer_narrative', e.target.value)}
            rows={4}
            placeholder="Describe what happened from the buyer's perspective…"
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Seller's Account</label>
          <textarea
            value={form.seller_narrative}
            onChange={e => set('seller_narrative', e.target.value)}
            rows={4}
            placeholder="Seller's response (optional at submission)"
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
        </div>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox" checked={autoInvestigate}
            onChange={e => setAutoInvestigate(e.target.checked)}
            className="w-4 h-4 rounded text-blue-600"
          />
          <span className="text-sm text-gray-700">Automatically run the Liquet autopilot after submission</span>
        </label>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3 text-sm text-red-700">{error}</div>
        )}

        <button
          type="submit" disabled={submitting}
          className="w-full bg-blue-700 text-white py-2.5 rounded-md font-medium hover:bg-blue-800 disabled:opacity-50 transition-colors"
        >
          {submitting ? 'Submitting…' : 'Submit Dispute'}
        </button>
      </form>
    </div>
  )
}
