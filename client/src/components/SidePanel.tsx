import { useEffect, useRef, type ReactNode } from 'react'
import { useI18n } from '../i18n/useI18n'
import './SidePanel.css'

interface SidePanelProps {
  label: string
  title: string
  titleLang?: string
  onClose: () => void
  children: ReactNode
}

export function SidePanel({ label, title, titleLang, onClose, children }: SidePanelProps) {
  const { t } = useI18n()
  const closeButton = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    closeButton.current?.focus()
  }, [])

  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [onClose])

  return (
    <aside className="side-panel" aria-label={label}>
      <div className="side-panel__top">
        <h2 className="serif" lang={titleLang}>
          {title}
        </h2>
        <button ref={closeButton} type="button" className="side-panel__close" aria-label={t('funds.close')} onClick={onClose}>
          ✕
        </button>
      </div>
      {children}
    </aside>
  )
}
