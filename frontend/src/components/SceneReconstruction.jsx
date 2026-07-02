import React, { useState, useRef } from 'react'

const POLL_MS = 3000
const MAX_POLLS = 30

export default function SceneReconstruction({ disputeId, decision }) {
  const [state, setState] = useState('idle') // idle | submitting | polling | done | failed | error
  const [imageUrl, setImageUrl] = useState(null)
  const [promptPreview, setPromptPreview] = useState('')
  const [pollCount, setPollCount] = useState(0)
  const [error, setError] = useState(null)
  const taskRef = useRef(null)
  const timerRef = useRef(null)

  const stopPolling = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }

  const pollTask = async (taskId, count = 0) => {
    if (count >= MAX_POLLS) {
      stopPolling()
      setState('error')
      setError('Scene generation timed out')
      return
    }
    try {
      const r = await fetch(`/api/cases/${disputeId}/scene?task_id=${taskId}`)
      const data = await r.json()
      setPollCount(count)

      if (data.status === 'succeeded') {
        stopPolling()
        setImageUrl(data.image_url)
        setState('done')
      } else if (data.status === 'failed') {
        stopPolling()
        setState('failed')
        setError(data.error || 'Generation failed')
      }
      // else still pending — keep polling
    } catch (err) {
      stopPolling()
      setState('error')
      setError(err.message)
    }
  }

  const generate = async () => {
    setState('submitting')
    setError(null)
    try {
      const r = await fetch(`/api/cases/${disputeId}/visualize`, { method: 'POST' })
      if (!r.ok) {
        const err = await r.json()
        throw new Error(err.detail || 'Failed to start generation')
      }
      const data = await r.json()

      if (data.status === 'cached' && data.image_url) {
        setImageUrl(data.image_url)
        setState('done')
        return
      }

      taskRef.current = data.task_id
      setPromptPreview(data.prompt_preview || '')
      setState('polling')
      setPollCount(0)

      let count = 0
      timerRef.current = setInterval(() => {
        count++
        pollTask(taskRef.current, count)
      }, POLL_MS)
    } catch (err) {
      setState('error')
      setError(err.message)
    }
  }

  if (!decision) return null

  const progressPct = Math.min(100, Math.round((pollCount / MAX_POLLS) * 100))

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-700 p-5 mb-6">
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl">🎨</span>
            <h3 className="font-bold text-white">Scene Reconstruction</h3>
            <span className="text-xs bg-purple-900/60 text-purple-300 px-2 py-0.5 rounded font-mono border border-purple-700">
              wan2.6-t2i
            </span>
          </div>
          <p className="text-xs text-gray-400 mt-0.5">AI-generated visual of this dispute scenario</p>
        </div>
        {state === 'idle' && (
          <button
            onClick={generate}
            className="bg-purple-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-purple-700 transition-colors flex items-center gap-2"
          >
            <span>🎨</span> Generate Scene
          </button>
        )}
      </div>

      {state === 'submitting' && (
        <div className="flex items-center gap-3 py-4">
          <div className="w-5 h-5 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-gray-400">Submitting to wan2.6-t2i…</span>
        </div>
      )}

      {state === 'polling' && (
        <div className="py-3">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-5 h-5 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-gray-400">
              Generating scene… ({pollCount * POLL_MS / 1000}s elapsed)
            </span>
          </div>
          <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden mb-3">
            <div
              className="h-full bg-gradient-to-r from-purple-600 to-blue-500 rounded-full transition-all duration-500"
              style={{ width: `${progressPct}%` }}
            />
          </div>
          {promptPreview && (
            <p className="text-xs text-gray-500 italic">"{promptPreview}…"</p>
          )}
        </div>
      )}

      {state === 'done' && imageUrl && (
        <div className="relative rounded-lg overflow-hidden border border-gray-700">
          <img
            src={imageUrl}
            alt="AI-reconstructed dispute scene"
            className="w-full object-cover"
            style={{ maxHeight: '400px' }}
          />
          <div className="absolute top-2 left-2 flex items-center gap-1.5 bg-black/60 backdrop-blur-sm rounded px-2 py-1">
            <span className="text-xs text-purple-300 font-mono">wan2.6-t2i</span>
            <span className="text-xs text-gray-300">AI Scene Reconstruction</span>
          </div>
          <div className="absolute bottom-2 right-2">
            <a
              href={imageUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-black/60 backdrop-blur-sm text-white text-xs px-2 py-1 rounded hover:bg-black/80 transition-colors"
            >
              View full ↗
            </a>
          </div>
        </div>
      )}

      {(state === 'error' || state === 'failed') && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-3 text-sm text-red-300 flex items-start justify-between">
          <span><span className="font-medium">Scene generation failed:</span> {error}</span>
          <button
            onClick={() => { setState('idle'); setError(null); stopPolling() }}
            className="ml-3 text-red-400 hover:text-red-200 underline whitespace-nowrap"
          >
            Retry
          </button>
        </div>
      )}
    </div>
  )
}
