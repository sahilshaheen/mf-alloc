import { useId } from 'react'

export function Sealed() {
  const id = useId().replace(/:/g, '')
  const shadow = `${id}shadow`
  return (
    <svg viewBox="0 0 520 400" width="100%" aria-hidden="true" style={{ display: 'block' }}>
      <defs>
        <filter id={shadow} x="-10%" y="-10%" width="130%" height="140%">
          <feDropShadow dx="0" dy="6" stdDeviation="7" floodColor="#14201c" floodOpacity="0.16" />
        </filter>
      </defs>
      <ellipse cx="258" cy="206" rx="238" ry="176" fill="none" stroke="var(--ink3)" strokeOpacity="0.55" strokeWidth="1.5" strokeDasharray="3 7" strokeLinecap="round" />
      <g filter={`url(#${shadow})`}>
        <rect x="201" y="14" width="50" height="66" rx="4" fill="var(--sheet)" stroke="var(--ink)" strokeWidth="1.6" />
        <path d="M210 28h32M210 37h32M210 46h22M210 55h28" stroke="var(--ink3)" strokeOpacity="0.6" strokeWidth="2.4" strokeLinecap="round" />
      </g>
      <path d="M186 26v24M266 26v24" stroke="var(--ink3)" strokeOpacity="0.55" strokeWidth="2" strokeLinecap="round" />
      <g filter={`url(#${shadow})`}>
        <rect x="96" y="70" width="260" height="200" rx="12" fill="var(--sheet)" stroke="var(--ink)" strokeWidth="2" />
        <path d="M56 270h340l18 22a6 6 0 0 1-5 9H43a6 6 0 0 1-5-9z" fill="var(--sheet)" stroke="var(--ink)" strokeWidth="2" strokeLinejoin="round" />
      </g>
      <rect x="112" y="86" width="228" height="168" rx="6" fill="var(--paper)" />
      <path d="M194 70h64" stroke="var(--ink)" strokeWidth="3.5" strokeLinecap="round" />
      <path d="M208 168v-16a18 18 0 0 1 36 0v16" fill="none" stroke="var(--ink)" strokeWidth="6" />
      <rect x="194" y="166" width="64" height="50" rx="8" fill="var(--ink)" />
      <circle cx="226" cy="186" r="5.5" fill="var(--onink)" />
      <rect x="223.5" y="188" width="5" height="12" rx="2" fill="var(--onink)" />
      <g transform="translate(142 232)">
        <rect width="74" height="8" rx="2" fill="var(--eq)" />
        <rect x="76" width="36" height="8" fill="var(--debt)" />
        <rect x="114" width="34" height="8" fill="var(--cash)" />
        <rect x="150" width="18" height="8" rx="2" fill="var(--gold)" />
      </g>
      <g filter={`url(#${shadow})`}>
        <rect x="404" y="176" width="58" height="118" rx="11" fill="var(--sheet)" stroke="var(--ink)" strokeWidth="2" />
      </g>
      <rect x="411" y="188" width="44" height="94" rx="5" fill="var(--paper)" />
      <path d="M425 232v-6a8 8 0 0 1 16 0v6" fill="none" stroke="var(--ink)" strokeWidth="3" />
      <rect x="419" y="231" width="28" height="22" rx="4" fill="var(--ink)" />
    </svg>
  )
}
