import React, { useState } from 'react'

export default function ReviewerNotes({ disputeId, auditTrail, onNoteAdded }) {
  const [open, setOpen] = useState(false)
  const [note, setNote] = useState('')
  const [reviewerId, setReviewerId] = useState('reviewer-01')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const existingNotes = (auditTrail || []).filter(e => e.event === 'reviewer_note')

  const submit = async () => {
    if (!note.trim()) return
    setSaving(true)
    setError(null)
    try {
      const r = await fetch(`/api/cases/${disputeId}/notes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reviewer_id: reviewerId, note: note.trim() }),
      })
      if (!r.ok) throw new Error((await r.json()).detail || 'Failed to save note')
      setNote('')
      setOpen(false)
      onNoteAdded?.()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-bold text-gray-900">
          Reviewer Notes
          {existingNotes.length > 0 && (
            <span className="ml-2 text-xs text-gray-400 font-normal">({existingNotes.length})</span>
          )}
        </h2>
        <button
          onClick={() => setOpen(o => !o)}
          className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 px-2 py-1 rounded border border-gray-300 transition-colors"
        >
          {open ? 'Cancel' : '+ Add Note'}
        </button>
      </div>

      {existingNotes.length > 0 && (
        <div className="space-y-2 mb-3">
          {existingNotes.map(e => (
            <div key={e.id} className="bg-amber-50 border border-amber-100 rounded-lg px-3 py-2 text-sm">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-medium text-amber-700">{e.actor_id || 'Reviewer'}</span>
                <span className="text-xs text-gray-400">{new Date(e.timestamp).toLocaleString()}</span>
              </div>
              <p className="text-gray-700">{e.data?.note}</p>
            </div>
          ))}
        </div>
      )}

      {existingNotes.length === 0 && !open && (
        <p className="text-sm text-gray-400">No reviewer notes yet.</p>
      )}

      {open && (
        <div className="space-y-2">
          <input
            type="text"
            value={reviewerId}
            onChange={e => setReviewerId(e.target.value)}
            placeholder="Reviewer ID"
            className="w-full border border-gray-300 rounded-md px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <textarea
            value={note}
            onChange={e => setNote(e.target.value)}
            rows={3}
            placeholder="Add a note for this case…"
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            autoFocus
          />
          {error && <p className="text-xs text-red-600">{error}</p>}
          <button
            onClick={submit}
            disabled={saving || !note.trim()}
            className="px-3 py-1.5 bg-amber-600 text-white text-xs rounded hover:bg-amber-700 disabled:opacity-50"
          >
            {saving ? 'Saving…' : 'Save Note'}
          </button>
        </div>
      )}
    </div>
  )
}
