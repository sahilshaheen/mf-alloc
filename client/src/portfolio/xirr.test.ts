import { describe, expect, it } from 'vitest'
import { xirr } from './xirr'

describe('xirr', () => {
  it('matches the worked example in Microsoft’s XIRR documentation', () => {
    const flows = [
      { date: '2008-01-01', amount: -10_000 },
      { date: '2008-03-01', amount: 2_750 },
      { date: '2008-10-30', amount: 4_250 },
      { date: '2009-02-15', amount: 3_250 },
      { date: '2009-04-01', amount: 2_750 },
    ]
    expect(xirr(flows)).toBeCloseTo(0.373362535, 6)
  })

  it('weights each instalment by how long it was invested', () => {
    const flows = [
      { date: '2022-01-01', amount: -100_000 },
      { date: '2023-01-01', amount: -100_000 },
      { date: '2024-01-01', amount: 230_000 },
    ]
    // 1e5·x² + 1e5·x = 2.3e5, with x = 1 + rate
    expect(xirr(flows)).toBeCloseTo((Math.sqrt(10.2) - 1) / 2 - 1, 6)
  })

  it('finds a negative rate for a loss', () => {
    expect(xirr([{ date: '2022-01-01', amount: -100_000 }, { date: '2023-01-01', amount: 80_000 }])).toBeCloseTo(-0.2, 6)
  })

  it('has no answer when money only goes one way', () => {
    expect(xirr([{ date: '2022-01-01', amount: -100 }, { date: '2023-01-01', amount: -100 }])).toBeNull()
  })
})
