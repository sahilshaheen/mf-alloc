import { describe, expect, it } from 'vitest'
import { segmentLayout } from './segmentLayout'

describe('segmentLayout', () => {
  it('gives each part a width in proportion to its value, with a fixed gap between parts', () => {
    expect(segmentLayout([60, 30, 10], 204, 2, 1)).toEqual([
      { left: 0, width: 120 },
      { left: 122, width: 60 },
      { left: 184, width: 20 },
    ])
  })

  it('snaps tiny parts to whole pixels at a minimum width, so every gap renders the same', () => {
    const boxes = segmentLayout([923, 20, 30, 12, 10], 360, 2, 4)
    for (const box of boxes) {
      expect(Number.isInteger(box.left)).toBe(true)
      expect(Number.isInteger(box.width)).toBe(true)
      expect(box.width).toBeGreaterThanOrEqual(4)
    }
    for (let index = 1; index < boxes.length; index++) {
      expect(boxes[index].left - (boxes[index - 1].left + boxes[index - 1].width)).toBe(2)
    }
    const last = boxes[boxes.length - 1]
    expect(last.left + last.width).toBe(360)
  })
})
