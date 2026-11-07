import { useId } from 'react'

export function LogoMark({ size = 26 }: { size?: number }) {
  const clipId = useId()
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      <defs>
        <clipPath id={clipId}>
          <circle cx="20" cy="16.5" r="7.2" />
        </clipPath>
      </defs>
      <rect x="2" y="6" width="22" height="4.5" rx="1.6" fill="var(--ink)" />
      <rect x="2" y="13.5" width="22" height="4.5" rx="1.6" fill="var(--ink)" />
      <rect x="2" y="21" width="22" height="4.5" rx="1.6" fill="var(--ink)" />
      <circle cx="20" cy="16.5" r="9.6" fill="var(--paper)" />
      <g clipPath={`url(#${clipId})`}>
        <rect x="10" y="6" width="22" height="4.5" fill="var(--eq)" />
        <rect x="10" y="13.5" width="22" height="4.5" fill="var(--debt)" />
        <rect x="10" y="21" width="22" height="4.5" fill="var(--cash)" />
      </g>
      <circle cx="20" cy="16.5" r="8.2" fill="none" stroke="var(--ink)" strokeWidth="2" />
      <path d="M25.9 22.4 L29.6 26.1" stroke="var(--ink)" strokeWidth="2.6" strokeLinecap="round" />
    </svg>
  )
}
