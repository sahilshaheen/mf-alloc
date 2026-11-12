import { scaleLinear } from 'd3-scale'
import './GainBar.css'

/** One row's gain or loss drawn from a zero line shared by every row; `extent` is the least and greatest gain in the list. */
export function GainBar({ value, extent }: { value: number; extent: [number, number] }) {
  const scale = scaleLinear()
    .domain([Math.min(0, extent[0]), Math.max(0, extent[1])])
    .range([0, 100])
  const zero = scale(0)
  const end = scale(value)
  return (
    <span className="gain-bar" aria-hidden="true">
      <span className={value < 0 ? 'gain-bar__fill gain-bar__fill--loss' : 'gain-bar__fill'} style={{ left: `${Math.min(zero, end)}%`, width: `${Math.abs(end - zero)}%` }} />
      <span className="gain-bar__zero" style={{ left: `${zero}%` }} />
    </span>
  )
}
