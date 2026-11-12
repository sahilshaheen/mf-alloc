import { segmentLayout } from './segmentLayout'
import { useWidth } from './useWidth'
import './SegmentedBar.css'

export interface BarPart {
  key: string
  value: number
  fill: string
  /** Full description for hover, focus and screen readers: name, share, amount. */
  title: string
  /** Printed inside the block when it fits; tall bars only. */
  label?: string
  lightText?: boolean
}

interface SegmentedBarProps {
  parts: BarPart[]
  size: 'tall' | 'thin'
  label: string
  activeKey?: string
  onActivate?: (key: string) => void
}

const GAP = 2
const LABEL_CHAR_WIDTH = 8.5
const LABEL_PADDING = 20

export function SegmentedBar({ parts, size, label, activeKey, onActivate }: SegmentedBarProps) {
  const { ref, width } = useWidth<HTMLDivElement>()
  const drawn = parts.filter((part) => part.value > 0)
  const boxes = width > 0 ? segmentLayout(drawn.map((part) => part.value), width, GAP) : []

  return (
    <div ref={ref} className={`segbar segbar--${size}`} role={onActivate ? 'group' : 'img'} aria-label={label}>
      {boxes.map((box, index) => {
        const part = drawn[index]
        const fits = part.label !== undefined && box.width >= part.label.length * LABEL_CHAR_WIDTH + LABEL_PADDING
        const style = { left: box.left, width: box.width, background: part.fill, color: part.lightText ? '#ffffff' : '#1b2422' }
        const text = size === 'tall' && fits ? part.label : null
        return onActivate ? (
          <button
            key={part.key}
            type="button"
            className="segbar__part"
            style={style}
            title={part.title}
            aria-label={part.title}
            aria-pressed={part.key === activeKey}
            onClick={() => onActivate(part.key)}
            onFocus={() => onActivate(part.key)}
            onPointerEnter={(event) => event.pointerType === 'mouse' && onActivate(part.key)}
          >
            {text}
          </button>
        ) : (
          <span key={part.key} className="segbar__part" style={style} title={part.title}>
            {text}
          </span>
        )
      })}
    </div>
  )
}
