import { describe, expect, it } from 'vitest'
import { sortRows } from './sortRows'

const rows = [
  { name: 'beta', gain: 5 },
  { name: 'Alpha', gain: null },
  { name: 'gamma', gain: -2 },
  { name: 'delta', gain: 10 },
]

describe('sortRows', () => {
  it.each([
    ['ascending', ['gamma', 'beta', 'delta', 'Alpha']],
    ['descending', ['delta', 'beta', 'gamma', 'Alpha']],
  ] as const)('sorts numbers %s with missing values last', (direction, expected) => {
    expect(sortRows(rows, (row) => row.gain, direction).map((row) => row.name)).toEqual(expected)
  })

  it('sorts text ignoring case', () => {
    expect(sortRows(rows, (row) => row.name, 'ascending').map((row) => row.name)).toEqual(['Alpha', 'beta', 'delta', 'gamma'])
  })
})
