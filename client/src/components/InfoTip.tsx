import { useEffect, useId, useRef, useState, type CSSProperties } from 'react'
import { createPortal } from 'react-dom'
import './InfoTip.css'

const GAP = 6
const EDGE = 8
const MAX_WIDTH = 300

// Portalled to <body> with fixed positioning: ancestors' transform animations (fill-mode: both) would
// otherwise become the containing block, and scrolling containers would clip the bubble.
function bubblePosition(anchor: DOMRect): CSSProperties {
  const width = Math.min(MAX_WIDTH, window.innerWidth - 2 * EDGE)
  const left = Math.max(EDGE, Math.min(anchor.left - EDGE, window.innerWidth - EDGE - width))
  const below = anchor.bottom < window.innerHeight * 0.6
  return below ? { left, top: anchor.bottom + GAP, maxWidth: width } : { left, bottom: window.innerHeight - anchor.top + GAP, maxWidth: width }
}

export function InfoTip({ label, text }: { label: string; text: string }) {
  const [anchor, setAnchor] = useState<DOMRect | null>(null)
  const button = useRef<HTMLButtonElement>(null)
  const id = useId()
  const show = () => setAnchor(button.current?.getBoundingClientRect() ?? null)
  const hide = () => setAnchor(null)

  useEffect(() => {
    if (!anchor) return
    const close = () => setAnchor(null)
    const hideOnEscape = (event: KeyboardEvent) => event.key === 'Escape' && close()
    window.addEventListener('scroll', close, true)
    window.addEventListener('resize', close)
    window.addEventListener('keydown', hideOnEscape)
    return () => {
      window.removeEventListener('scroll', close, true)
      window.removeEventListener('resize', close)
      window.removeEventListener('keydown', hideOnEscape)
    }
  }, [anchor])

  return (
    <>
      <button
        ref={button}
        type="button"
        className="info-tip"
        aria-label={label}
        aria-describedby={id}
        onMouseEnter={show}
        onMouseLeave={hide}
        onFocus={show}
        onBlur={hide}
        onClick={show}
      >
        i
      </button>
      {createPortal(
        <span role="tooltip" id={id} className="info-tip__bubble" hidden={!anchor} style={anchor ? bubblePosition(anchor) : undefined}>
          {text}
        </span>,
        document.body,
      )}
    </>
  )
}
