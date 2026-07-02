import React, { useEffect, useRef, useState } from 'react'

const CHAR_DELAY_MS = 8

function useTypewriter(text, active) {
  const [displayed, setDisplayed] = useState('')
  const posRef = useRef(0)
  const prevTextRef = useRef('')

  useEffect(() => {
    if (!active) return
    if (text === prevTextRef.current) return

    const newChars = text.slice(prevTextRef.current.length)
    prevTextRef.current = text
    let i = 0
    const id = setInterval(() => {
      if (i >= newChars.length) {
        clearInterval(id)
        return
      }
      setDisplayed(prev => prev + newChars[i])
      i++
    }, CHAR_DELAY_MS)
    return () => clearInterval(id)
  }, [text, active])

  return displayed
}

export default function ReasoningGlass({ disputeId, decision }) {
  const [state, setState] = useState('idle') // idle | connecting | thinking | answering | done | error
  const [thinkingText, setThinkingText] = useState('')
  const [verdictText, setVerdictText] = useState('')
  const [thinkingLen, setThinkingLen] = useState(0)
  const [error, setError] = useState(null)
  const [tab, setTab] = useState('thinking') // thinking | verdict
  const wsRef = useRef(null)
  const thinkBoxRef = useRef(null)
  const verdictBoxRef = useRef(null)
  const thinkRawRef = useRef('')
  const verdictRawRef = useRef('')

  const displayedThinking = useTypewriter(thinkingText, state === 'thinking' || state === 'answering' || state === 'done')
  const displayedVerdict = useTypewriter(verdictText, state === 'answering' || state === 'done')

  const start = () => {
    if (wsRef.current) return
    setState('connecting')
    setThinkingText('')
    setVerdictText('')
    thinkRawRef.current = ''
    verdictRawRef.current = ''

    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(`${proto}://${window.location.host}/ws/disputes/${disputeId}/think`)
    wsRef.current = ws

    ws.onopen = () => setState('thinking')

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data)
        if (msg.type === 'thinking') {
          thinkRawRef.current += msg.content
          setThinkingText(thinkRawRef.current)
          if (thinkBoxRef.current) {
            thinkBoxRef.current.scrollTop = thinkBoxRef.current.scrollHeight
          }
        } else if (msg.type === 'verdict') {
          if (tab === 'thinking') setTab('verdict')
          verdictRawRef.current += msg.content
          setVerdictText(verdictRawRef.current)
          setState('answering')
        } else if (msg.type === 'done') {
          setThinkingLen(msg.thinking_length || 0)
          setState('done')
        } else if (msg.type === 'error') {
          setError(msg.message)
          setState('error')
        }
      } catch {
        // ignore parse errors
      }
    }

    ws.onerror = () => {
      setError('WebSocket connection failed')
      setState('error')
      wsRef.current = null
    }

    ws.onclose = () => {
      wsRef.current = null
      if (state !== 'done' && state !== 'error') {
        setState(s => s === 'thinking' || s === 'answering' ? 'done' : s)
      }
    }
  }

  const reset = () => {
    wsRef.current?.close()
    wsRef.current = null
    setState('idle')
    setThinkingText('')
    setVerdictText('')
    setError(null)
    thinkRawRef.current = ''
    verdictRawRef.current = ''
  }

  useEffect(() => () => wsRef.current?.close(), [])

  if (!decision) return null

  const isRunning = state === 'connecting' || state === 'thinking' || state === 'answering'
  const tokenCount = thinkingText.split(/\s+/).filter(Boolean).length

  return (
    <div className="bg-[#0d1117] rounded-xl border border-gray-700 p-5 mb-6 font-mono">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-green-400 text-lg">⬡</span>
            <h3 className="font-bold text-green-400">Reasoning Glass</h3>
            <span className="text-xs bg-green-900/40 text-green-400 px-2 py-0.5 rounded border border-green-800">
              qwen3.7-max
            </span>
            {isRunning && (
              <span className="flex items-center gap-1 text-xs text-green-500 animate-pulse">
                <span className="w-1.5 h-1.5 rounded-full bg-green-500 inline-block" />
                LIVE
              </span>
            )}
            {state === 'done' && thinkingLen > 0 && (
              <span className="text-xs text-gray-500">
                {thinkingLen.toLocaleString()} thinking chars
              </span>
            )}
          </div>
          <p className="text-xs text-gray-500 mt-0.5">Watch qwen3.7-max reason through the evidence in real time</p>
        </div>

        <div className="flex items-center gap-2">
          {state === 'idle' && (
            <button
              onClick={start}
              className="bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-green-600 transition-colors flex items-center gap-2"
            >
              <span>⬡</span> Start Thinking
            </button>
          )}
          {state === 'done' && (
            <button
              onClick={reset}
              className="text-xs text-gray-500 hover:text-gray-300 border border-gray-700 px-3 py-1 rounded"
            >
              ↺ Re-run
            </button>
          )}
          {isRunning && (
            <button
              onClick={reset}
              className="text-xs text-red-400 hover:text-red-300 border border-red-900 px-3 py-1 rounded"
            >
              ✕ Stop
            </button>
          )}
        </div>
      </div>

      {state === 'connecting' && (
        <div className="text-green-500 text-sm py-3 flex items-center gap-2">
          <span className="inline-block animate-spin">◌</span>
          Connecting to qwen3.7-max with extended thinking…
        </div>
      )}

      {/* Terminal body */}
      {(state === 'thinking' || state === 'answering' || state === 'done') && (
        <div>
          {/* Tabs */}
          {verdictText && (
            <div className="flex gap-1 mb-2">
              <button
                onClick={() => setTab('thinking')}
                className={`text-xs px-3 py-1 rounded-t border-b-2 transition-colors ${
                  tab === 'thinking'
                    ? 'text-yellow-400 border-yellow-500 bg-yellow-900/20'
                    : 'text-gray-500 border-transparent hover:text-gray-300'
                }`}
              >
                🧠 Thinking {tokenCount > 0 && `(~${tokenCount} words)`}
              </button>
              <button
                onClick={() => setTab('verdict')}
                className={`text-xs px-3 py-1 rounded-t border-b-2 transition-colors ${
                  tab === 'verdict'
                    ? 'text-green-400 border-green-500 bg-green-900/20'
                    : 'text-gray-500 border-transparent hover:text-gray-300'
                }`}
              >
                ✓ Verdict
              </button>
            </div>
          )}

          {tab === 'thinking' && (
            <div
              ref={thinkBoxRef}
              className="bg-black/40 rounded border border-gray-800 p-4 h-72 overflow-y-auto text-xs leading-relaxed text-yellow-200/80 whitespace-pre-wrap"
              style={{ fontFamily: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace" }}
            >
              {displayedThinking || <span className="text-gray-600">Thinking tokens will appear here…</span>}
              {isRunning && <span className="animate-pulse text-green-400">▊</span>}
            </div>
          )}

          {tab === 'verdict' && verdictText && (
            <div
              ref={verdictBoxRef}
              className="bg-black/40 rounded border border-gray-800 p-4 h-72 overflow-y-auto text-xs leading-relaxed text-green-200 whitespace-pre-wrap"
              style={{ fontFamily: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace" }}
            >
              {displayedVerdict}
              {state === 'answering' && <span className="animate-pulse text-green-400">▊</span>}
            </div>
          )}

          {state === 'done' && (
            <div className="mt-2 flex items-center justify-between text-xs text-gray-600">
              <span>Reasoning complete · {new Date().toLocaleTimeString()}</span>
              <span>{thinkingLen.toLocaleString()} thinking chars → {verdictText.length} verdict chars</span>
            </div>
          )}
        </div>
      )}

      {state === 'error' && (
        <div className="bg-red-900/30 border border-red-800 rounded p-3 text-sm text-red-400 flex items-start justify-between">
          <span>{error}</span>
          <button onClick={reset} className="ml-3 underline text-red-400 hover:text-red-200">
            Retry
          </button>
        </div>
      )}
    </div>
  )
}
