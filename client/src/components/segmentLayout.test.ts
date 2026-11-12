import { describe, expect, it } from 'vitest'
import { segmentLayout } from './segmentLayout'

describe('segmentLayout', () => {
  it('gives each part a width in proportion to its value, with a fixed gap between parts', () => {
    expect(segmentLayout([60, 30, 10], 204, 2)).toEqual([
      { left: 0, width: 120 },
      { left: 122, width: 60 },
      { left: 184, width: 20 },
    ])
  })
})
