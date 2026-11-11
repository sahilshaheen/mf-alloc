import type { ReactNode } from 'react'
import type { SortDirection } from '../sortRows'
import type { Sort } from './useSort'
import './SortableHeader.css'

interface SortableHeaderProps<Column extends string> {
  column: Column
  label: string
  sort: Sort<Column>
  /** Text columns start A to Z; number columns start largest first. */
  firstDirection: SortDirection
  onSort: (column: Column, firstDirection: SortDirection) => void
  className?: string
  children?: ReactNode
}

export function SortableHeader<Column extends string>({ column, label, sort, firstDirection, onSort, className, children }: SortableHeaderProps<Column>) {
  const active = sort.column === column
  return (
    <span role="columnheader" aria-sort={active ? sort.direction : undefined} className={className}>
      <button type="button" className="sortable-header" onClick={() => onSort(column, firstDirection)}>
        {label}
        <span aria-hidden="true" className="sortable-header__arrow">
          {active ? (sort.direction === 'ascending' ? '↑' : '↓') : '↕'}
        </span>
      </button>
      {children}
    </span>
  )
}
