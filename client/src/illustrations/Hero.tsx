import { useId } from 'react'

export function Hero() {
  const id = useId().replace(/:/g, '')
  const shadow = `${id}shadow`
  const hole = `${id}hole`
  return (
    <svg viewBox="0 0 600 460" width="100%" aria-hidden="true" style={{ display: 'block' }}>
      <defs>
        <filter id={shadow} x="-10%" y="-10%" width="130%" height="140%">
          <feDropShadow dx="0" dy="6" stdDeviation="7" floodColor="#14201c" floodOpacity="0.16" />
        </filter>
        <clipPath id={hole}>
          <circle cx="262" cy="140" r="72" />
        </clipPath>
      </defs>
      <g transform="translate(214 176) rotate(5)" filter={`url(#${shadow})`}>
        <rect width="360" height="246" rx="12" fill="var(--gold)" />
      </g>
      <g transform="translate(190 148) rotate(3)" filter={`url(#${shadow})`}>
        <rect width="360" height="246" rx="12" fill="var(--cash)" />
      </g>
      <g transform="translate(166 120) rotate(1.2)" filter={`url(#${shadow})`}>
        <rect width="360" height="246" rx="12" fill="var(--debt)" />
      </g>
      <g transform="translate(142 92) rotate(-0.6)" filter={`url(#${shadow})`}>
        <rect width="360" height="246" rx="12" fill="var(--eq)" />
      </g>
      <g transform="translate(96 58) rotate(-2.2)">
        <g clipPath={`url(#${hole})`}>
          <rect x="180" y="60" width="170" height="54" fill="var(--eq)" />
          <rect x="180" y="116" width="170" height="34" fill="var(--debt)" />
          <rect x="180" y="152" width="170" height="34" fill="var(--cash)" />
          <rect x="180" y="188" width="170" height="40" fill="var(--gold)" />
          <path d="M190 114h150M190 150h150M190 186h150" stroke="var(--sheet)" strokeWidth="2" />
          <circle cx="262" cy="140" r="72" fill="none" stroke="#000" strokeOpacity="0.12" strokeWidth="10" />
        </g>
        <path
          d="M12 0h356a12 12 0 0 1 12 12v236a12 12 0 0 1-12 12H12A12 12 0 0 1 0 248V12A12 12 0 0 1 12 0z M262 68a72 72 0 1 0 0.01 0z"
          fill="var(--sheet)"
          fillRule="evenodd"
          filter={`url(#${shadow})`}
        />
        <rect x="26" y="28" width="132" height="12" rx="3" fill="var(--ink)" opacity="0.85" />
        <rect x="26" y="58" width="150" height="6" rx="3" fill="var(--ink3)" opacity="0.35" />
        <rect x="26" y="74" width="124" height="6" rx="3" fill="var(--ink3)" opacity="0.35" />
        <rect x="26" y="90" width="140" height="6" rx="3" fill="var(--ink3)" opacity="0.35" />
        <rect x="26" y="106" width="96" height="6" rx="3" fill="var(--ink3)" opacity="0.35" />
        <rect x="26" y="150" width="112" height="28" rx="14" fill="none" stroke="var(--ink)" strokeWidth="1.6" />
        <rect x="42" y="161" width="80" height="6" rx="3" fill="var(--ink)" opacity="0.7" />
        <g transform="translate(26 214)">
          <rect width="78" height="12" rx="2" fill="var(--t4)" />
          <rect x="80" width="46" height="12" fill="var(--t2)" />
          <rect x="128" width="30" height="12" rx="2" fill="var(--t4)" />
        </g>
        <circle cx="262" cy="140" r="77" fill="none" stroke="var(--ink)" strokeWidth="3.5" />
        <path d="M210 104a62 62 0 0 1 40-26" fill="none" stroke="var(--onink)" strokeOpacity="0.55" strokeWidth="5" strokeLinecap="round" />
        <path d="M318 196l58 58" stroke="var(--ink)" strokeWidth="12" strokeLinecap="round" />
      </g>
    </svg>
  )
}
