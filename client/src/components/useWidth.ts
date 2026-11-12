import { useEffect, useRef, useState } from 'react'

/** A ref for an element and its content width in pixels, kept current as the layout changes; 0 until measured. */
export function useWidth<Element extends HTMLElement>() {
  const ref = useRef<Element>(null)
  const [width, setWidth] = useState(0)
  useEffect(() => {
    const observer = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width))
    observer.observe(ref.current!)
    return () => observer.disconnect()
  }, [])
  return { ref, width }
}
