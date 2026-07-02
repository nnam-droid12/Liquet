import { useState } from 'react'

export default function useLocalStorage(key, defaultValue) {
  const [value, setValue] = useState(() => {
    try {
      const stored = window.localStorage.getItem(key)
      return stored !== null ? JSON.parse(stored) : defaultValue
    } catch {
      return defaultValue
    }
  })

  const set = (next) => {
    try {
      window.localStorage.setItem(key, JSON.stringify(next))
    } catch {}
    setValue(next)
  }

  return [value, set]
}
