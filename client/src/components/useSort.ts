import { useState } from 'react'
import type { SortDirection } from '../sortRows'

export interface Sort<Column extends string> {
  column: Column
  direction: SortDirection
}

export function useSort<Column extends string>(initial: Sort<Column>) {
  const [sort, setSort] = useState(initial)
  const sortBy = (column: Column, firstDirection: SortDirection) =>
    setSort((current) =>
      current.column === column
        ? { column, direction: current.direction === 'ascending' ? 'descending' : 'ascending' }
        : { column, direction: firstDirection },
    )
  return { sort, sortBy }
}
