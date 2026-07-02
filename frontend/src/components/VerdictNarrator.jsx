import React, { useEffect, useRef, useState } from 'react'

function WaveformBar({ active, height }) {
  return (
    <div
      className={`w-1 rounded-full transition-all duration-150 ${active ? 'bg-blue-400' : 'bg-blue-200'}`}
      style={{ height: `${height}px` }}
    />
  )
}

function Waveform({ playing }) {
  const [bars, setBars] = useState(Array.from({ length: 24 }, () => 8))

  useEffect(() => {
    if (!playing) {
      setBars(Array.from({ length: 24 }, () => 8))
      return
    }
    const id = setInterval(() => {
      setBars(prev => prev.map(() => playing ? Math.random() * 36 + 6 : 8))
    }, 120)
    return () => clearInterval(id)
  }, [playing])

  return (
    <div className="flex items-center gap-0.5 h-12">
      {bars.map((h, i) => <WaveformBar key={i} active={playing} height={h} />)}
    </div>
  )
}

export default function VerdictNarrator({ disputeId, decision }) {
  const [state, setState] = useState('idle') // idle | loading | ready | playing | error
  const [audioUrl, setAudioUrl] = useState(null)
  const [script, setScript] = useState('')
  const [error, setError] = useState(null)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const audioRef = useRef(null)

  const generate = async () => {
    setState('loading')
    setError(null)
    try {
      const r = await fetch(`/api/cases/${disputeId}/narrate`, { method: 'POST' })
      if (!r.ok) {
        const err = await r.json()
        throw new Error(err.detail || 'Failed to generate audio')
      }
      const data = await r.json()
      const blob = new Blob(
        [Uint8Array.from(atob(data.audio_b64), c => c.charCodeAt(0))],
        { type: 'audio/mpeg' }
      )
      setAudioUrl(URL.createObjectURL(blob))
      setScript(data.text)
      setState('ready')
    } catch (err) {
      setError(err.message)
      setState('error')
    }
  }

  const togglePlay = () => {
    const audio = audioRef.current
    if (!audio) return
    if (state === 'playing') {
      audio.pause()
      setState('ready')
    } else {
      audio.play()
      setState('playing')
    }
  }

  if (!decision) return null

  const isLiquet = decision.gate_result === 'LIQUET'

  return (
    <div className={`rounded-xl border p-5 mb-6 ${
      isLiquet
        ? 'bg-emerald-50 border-emerald-200'
        : 'bg-amber-50 border-amber-200'
    }`}>
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl">🔊</span>
            <h3 className="font-bold text-gray-900">Verdict Narration</h3>
            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded font-mono border border-blue-200">
              cosyvoice-v3-plus
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-0.5">Hear the AI arbitrator deliver the decision aloud</p>
        </div>
        {state === 'idle' && (
          <button
            onClick={generate}
            className="bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-blue-800 transition-colors flex items-center gap-2"
          >
            <span>🔊</span> Generate Audio
          </button>
        )}
      </div>

      {state === 'loading' && (
        <div className="flex items-center gap-3 py-4">
          <div className="flex gap-1">
            {[0, 1, 2, 3, 4].map(i => (
              <div
                key={i}
                className="w-1.5 h-6 bg-blue-400 rounded-full animate-pulse"
                style={{ animationDelay: `${i * 0.1}s` }}
              />
            ))}
          </div>
          <span className="text-sm text-gray-600">Synthesizing voice via CosyVoice v3 Plus…</span>
        </div>
      )}

      {(state === 'ready' || state === 'playing') && audioUrl && (
        <div>
          {/* Waveform + controls */}
          <div className="flex items-center gap-4 mb-3">
            <button
              onClick={togglePlay}
              className={`w-12 h-12 rounded-full flex items-center justify-center text-white text-xl shadow-md transition-all ${
                state === 'playing'
                  ? 'bg-blue-600 hover:bg-blue-700 scale-105'
                  : 'bg-blue-700 hover:bg-blue-800'
              }`}
            >
              {state === 'playing' ? '⏸' : '▶'}
            </button>
            <Waveform playing={state === 'playing'} />
            <span className="text-xs text-gray-400 font-mono w-16 text-right">
              {duration > 0 ? `${Math.floor(currentTime)}s / ${Math.floor(duration)}s` : ''}
            </span>
          </div>

          <audio
            ref={audioRef}
            src={audioUrl}
            onEnded={() => setState('ready')}
            onTimeUpdate={() => setCurrentTime(audioRef.current?.currentTime || 0)}
            onLoadedMetadata={() => setDuration(audioRef.current?.duration || 0)}
          />

          {/* Script */}
          {script && (
            <details className="mt-3">
              <summary className="text-xs text-gray-400 cursor-pointer hover:text-gray-600">
                View narration script
              </summary>
              <p className="mt-2 text-xs text-gray-600 bg-white/60 rounded p-3 leading-relaxed border border-white">
                {script}
              </p>
            </details>
          )}
        </div>
      )}

      {state === 'error' && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
          <span className="font-medium">Audio generation failed:</span> {error}
          <button onClick={generate} className="ml-3 underline text-red-600 hover:text-red-800">
            Retry
          </button>
        </div>
      )}
    </div>
  )
}
