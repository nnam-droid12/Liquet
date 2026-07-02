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

  const SCENARIOS = [
    {
      label: 'Clear LIQUET (never arrived)',
      form: {
        order_id: `ORD-D${Date.now().toString().slice(-4)}`,
        dispute_type: 'never_arrived',
        buyer_id: 'USR-B010',
        seller_id: 'USR-S010',
        buyer_narrative: 'My order was supposed to arrive 3 weeks ago. Tracking shows it got stuck at the sorting facility and was never delivered to me. I have waited patiently and the package has been marked lost by the carrier.',
        seller_narrative: 'I shipped the item on the date stated. The carrier lost it in transit — this is not my fault. I have the shipping receipt.',
      }
    },
    {
      label: '50/50 (hard contradiction)',
      form: {
        order_id: `ORD-D${Date.now().toString().slice(-4)}`,
        dispute_type: 'not_as_described',
        buyer_id: 'USR-B011',
        seller_id: 'USR-S001',
        buyer_narrative: 'I recorded my unboxing on video. The moment I removed the lens from the box it was visibly scratched on the front element. The scratch was there before I touched it. $649 for a damaged lens — I need a full refund.',
        seller_narrative: 'I have detailed inspection photos taken on the day of shipping. The glass was perfect. I\'ve been selling cameras for 8 years with zero complaints. The buyer must have caused the damage after unboxing.',
      }
    },
    {
      label: 'Clear NON LIQUET (high value)',
      form: {
        order_id: `ORD-D${Date.now().toString().slice(-4)}`,
        dispute_type: 'counterfeit',
        buyer_id: 'USR-B012',
        seller_id: 'USR-S002',
        buyer_narrative: 'I purchased what was advertised as an authentic Rolex watch for $2,500. The watch has several signs of being counterfeit: the logo is slightly off-center, the weight feels wrong, and the serial number does not verify on the Rolex website.',
        seller_narrative: 'The watch is completely authentic. I purchased it from an authorized dealer and have the original receipt and certificate of authenticity.',
      }
    },
  ]

  const loadDemo = (scenarioIdx = 1) => {
    setForm(SCENARIOS[scenarioIdx].form)
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">New Dispute</h1>
          <p className="text-gray-500 text-sm mt-1">Submit a marketplace dispute for Liquet to investigate</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          {SCENARIOS.map((s, i) => (
            <button
              key={i}
              type="button"
              onClick={() => loadDemo(i)}
              className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 px-2 py-1 rounded border border-gray-300 transition-colors"
            >
              Demo: {s.label}
            </button>
          ))}
        </div>
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
          <div className="flex justify-between items-center mb-1">
            <label className="text-sm font-medium text-gray-700">Buyer's Account *</label>
            <span className="text-xs text-gray-400">
              {form.buyer_narrative.trim().split(/\s+/).filter(Boolean).length} words
            </span>
          </div>
          <textarea
            required value={form.buyer_narrative}
            onChange={e => set('buyer_narrative', e.target.value)}
            rows={4}
            placeholder="Describe what happened from the buyer's perspective…"
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
        </div>

        <div>
          <div className="flex justify-between items-center mb-1">
            <label className="text-sm font-medium text-gray-700">Seller's Account</label>
            <span className="text-xs text-gray-400">
              {form.seller_narrative ? form.seller_narrative.trim().split(/\s+/).filter(Boolean).length + ' words' : 'optional'}
            </span>
          </div>
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
