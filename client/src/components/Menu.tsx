import { useEffect, useId, useRef, useState, type ReactNode } from 'react'
import './Menu.css'

export function Menu({ label, active = false, align = 'start', children }: { label: ReactNode; active?: boolean; align?: 'start' | 'end'; children: ReactNode }) {
  const [open, setOpen] = useState(false)
  const root = useRef<HTMLDivElement>(null)
  const id = useId()

  useEffect(() => {
    if (!open) return
    const closeOutside = (event: PointerEvent) => {
      if (!root.current?.contains(event.target as Node)) setOpen(false)
    }
    const closeOnEscape = (event: KeyboardEvent) => event.key === 'Escape' && setOpen(false)
    window.addEventListener('pointerdown', closeOutside)
    window.addEventListener('keydown', closeOnEscape)
    return () => {
      window.removeEventListener('pointerdown', closeOutside)
      window.removeEventListener('keydown', closeOnEscape)
    }
  }, [open])

  return (
    <div ref={root} className="menu">
      <button type="button" className={active ? 'menu__button active' : 'menu__button'} aria-expanded={open} aria-controls={id} onClick={() => setOpen(!open)}>
        {label}
        <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden="true">
          <path d="M2 3.5 5 6.5 8 3.5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
      <div id={id} className={`menu__items menu__items--${align}`} hidden={!open} onClick={() => setOpen(false)}>
        {children}
      </div>
    </div>
  )
}
