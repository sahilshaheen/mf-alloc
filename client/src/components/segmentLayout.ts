import { cumsum, sum } from 'd3-array'

export interface SegmentBox {
  left: number
  width: number
}

/**
 * Pixel boxes for the parts of one whole laid end to end, `gap` pixels apart. Edges fall on whole pixels,
 * because fractional edges anti-alias and make equal gaps look uneven; no part is narrower than `minWidth`.
 */
export function segmentLayout(values: number[], width: number, gap: number, minWidth: number): SegmentBox[] {
  const available = width - gap * (values.length - 1)
  const widths = proportionalWidths(values, available, minWidth)
  const ends = cumsum(widths)
  return widths.map((partWidth, index) => {
    const start = Math.round(ends[index] - partWidth)
    return { left: start + gap * index, width: Math.round(ends[index]) - start }
  })
}

function proportionalWidths(values: number[], available: number, minWidth: number): number[] {
  const atMinimum = new Set<number>()
  for (;;) {
    const scaledTotal = sum(values, (value, index) => (atMinimum.has(index) ? 0 : value))
    const scale = (available - atMinimum.size * minWidth) / scaledTotal
    const widths = values.map((value, index) => (atMinimum.has(index) ? minWidth : value * scale))
    const tooNarrow = widths.flatMap((partWidth, index) => (partWidth < minWidth && !atMinimum.has(index) ? [index] : []))
    if (tooNarrow.length === 0) return widths
    for (const index of tooNarrow) atMinimum.add(index)
  }
}
