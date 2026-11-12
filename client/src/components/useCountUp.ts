import { useEffect, useState } from 'react'

const DURATION_MS = 600
const easeOutCubic = (progress: number): number => 1 - (1 - progress) ** 3

/** Runs from zero up to `target` once, when first shown; the target itself where motion is reduced. */
export function useCountUp(target: number): number {
  const [shown, setShown] = useState(() => (window.matchMedia('(prefers-reduced-motion: reduce)').matches ? target : 0))

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const start = performance.now()
    let frame = requestAnimationFrame(function step(now) {
      const progress = Math.min(1, (now - start) / DURATION_MS)
      setShown(target * easeOutCubic(progress))
      if (progress < 1) frame = requestAnimationFrame(step)
    })
    return () => cancelAnimationFrame(frame)
  }, [target])

  return shown
}
