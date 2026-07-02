import React, { useState } from 'react'

export default function SellerReplyForm({ disputeId, currentNarrative, onSaved }) {
  const [open, setOpen] = useState(false)
  const [text, setText] = useState(currentNarrative || '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const save = async () => {
    if (!text.trim()) return
    setSaving(true)
    setError(null)
    try {
      const r = await fetch(`/api/disputes/${disputeId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ seller_narrative: text.trim() }),
      })
      if (!r.ok) throw new Error((await r.json()).detail || 'Failed to save')
      setOpen(false)
      onSaved?.()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="text-xs text-blue-600 hover:underline mt-1 inline-block"
      >
        {currentNarrative ? 'Edit seller response' : '+ Add seller response'}
      </button>
    )
  }

  return (
    <div className="mt-2 space-y-2">
      <textarea
        value={text}
        onChange={e => setText(e.target.value)}
        rows={4}
        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
        placeholder="Seller's response to this dispute…"
        autoFocus
      />
      {error && <p className="text-xs text-red-600">{error}</p>}
      <div className="flex gap-2">
        <button
          onClick={save}
          disabled={saving || !text.trim()}
          className="px-3 py-1.5 bg-blue-700 text-white text-xs rounded hover:bg-blue-800 disabled:opacity-50"
        >
          {saving ? 'Saving…' : 'Save'}
        </button>
        <button
          onClick={() => setOpen(false)}
          className="px-3 py-1.5 text-gray-600 text-xs rounded hover:bg-gray-100 border border-gray-300"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}
