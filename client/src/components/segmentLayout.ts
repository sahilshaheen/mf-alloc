import { cumsum, sum } from 'd3-array'
import { scaleLinear } from 'd3-scale'

export interface SegmentBox {
  left: number
  width: number
}

/** Pixel boxes for the parts of one whole laid end to end, `gap` pixels apart. */
export function segmentLayout(values: number[], width: number, gap: number): SegmentBox[] {
  const scale = scaleLinear()
    .domain([0, sum(values)])
    .range([0, width - gap * (values.length - 1)])
  const ends = cumsum(values)
  return values.map((value, index) => ({ left: scale(ends[index] - value) + gap * index, width: scale(value) }))
}
