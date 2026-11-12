import * as Dialog from '@radix-ui/react-dialog'
import { useSyncExternalStore, type ReactNode } from 'react'
import { useI18n } from '../i18n/useI18n'
import './SidePanel.css'

interface SidePanelProps {
  label: string
  title: string
  titleLang?: string
  onClose: () => void
  children: ReactNode
}

const sheetQuery = window.matchMedia('(max-width: 1100px)')
const subscribeToSheetQuery = (onChange: () => void) => {
  sheetQuery.addEventListener('change', onChange)
  return () => sheetQuery.removeEventListener('change', onChange)
}

/**
 * Beside the page on wide screens, where the page stays usable (clicking another row swaps the panel);
 * a modal full-screen sheet on narrow ones, where the page behind is locked so only the sheet scrolls.
 */
export function SidePanel({ label, title, titleLang, onClose, children }: SidePanelProps) {
  const { t } = useI18n()
  const isSheet = useSyncExternalStore(subscribeToSheetQuery, () => sheetQuery.matches)

  const content = (
    <Dialog.Content
      className="side-panel"
      aria-label={label}
      aria-describedby={undefined}
      onInteractOutside={(event) => !isSheet && event.preventDefault()}
    >
      <div className="side-panel__top">
        <Dialog.Title className="serif" lang={titleLang}>
          {title}
        </Dialog.Title>
        <Dialog.Close className="side-panel__close" aria-label={t('funds.close')}>
          ✕
        </Dialog.Close>
      </div>
      {children}
    </Dialog.Content>
  )

  return (
    <Dialog.Root open modal={isSheet} onOpenChange={(open) => !open && onClose()}>
      {isSheet ? <Dialog.Portal>{content}</Dialog.Portal> : content}
    </Dialog.Root>
  )
}
