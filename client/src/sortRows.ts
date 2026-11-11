/** Matches the values of the aria-sort attribute. */
export type SortDirection = 'ascending' | 'descending'
export type SortValue = number | string | null

export function sortRows<T>(rows: readonly T[], valueOf: (row: T) => SortValue, direction: SortDirection): T[] {
  const sign = direction === 'ascending' ? 1 : -1
  return [...rows].sort((a, b) => {
    const left = valueOf(a)
    const right = valueOf(b)
    if (left === null || right === null) return left === right ? 0 : left === null ? 1 : -1
    const order = typeof left === 'string' ? left.localeCompare(String(right), undefined, { sensitivity: 'base', numeric: true }) : left - Number(right)
    return sign * order
  })
}
