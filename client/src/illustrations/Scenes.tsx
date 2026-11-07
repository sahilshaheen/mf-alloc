import { useId, type ReactNode } from 'react'

function Scene({ children, shadowOpacity = 0.14, extraDefs }: { children: (shadow: string, id: string) => ReactNode; shadowOpacity?: number; extraDefs?: (id: string) => ReactNode }) {
  const id = useId().replace(/:/g, '')
  const shadow = `${id}shadow`
  return (
    <svg viewBox="0 0 400 300" width="100%" aria-hidden="true" style={{ display: 'block' }}>
      <defs>
        <filter id={shadow} x="-10%" y="-10%" width="130%" height="140%">
          <feDropShadow dx="0" dy="5" stdDeviation="6" floodColor="#14201c" floodOpacity={shadowOpacity} />
        </filter>
        {extraDefs?.(id)}
      </defs>
      {children(`url(#${shadow})`, id)}
    </svg>
  )
}

export function Processing() {
  return (
    <Scene shadowOpacity={0.16}>
      {(shadow) => (
        <g transform="translate(120 36)">
          <rect x="0" y="0" width="170" height="226" rx="6" fill="var(--eq)" />
          <rect x="0" y="78" width="170" height="54" fill="var(--debt)" />
          <rect x="0" y="134" width="170" height="46" fill="var(--cash)" />
          <rect x="0" y="182" width="170" height="44" fill="var(--gold)" />
          <path d="M0 77h170M0 133h170M0 181h170" stroke="var(--paper)" strokeWidth="2" />
          <path d="M6 0h70l94 112v108a6 6 0 0 1-6 6H6a6 6 0 0 1-6-6V6a6 6 0 0 1 6-6z" fill="var(--sheet)" stroke="var(--ink)" strokeWidth="1.6" filter={shadow} />
          <path d="M76 0L170 112Q126 108 106 78Q88 46 76 0z" fill="var(--t2)" stroke="var(--ink)" strokeWidth="1.6" strokeLinejoin="round" />
          <path
            d="M18 24h44M18 40h52M18 56h40M18 88h56M18 104h60M18 136h96M18 152h80M18 184h110M18 200h90"
            stroke="var(--ink3)"
            strokeOpacity="0.45"
            strokeWidth="5"
            strokeLinecap="round"
          />
        </g>
      )}
    </Scene>
  )
}

export function EmptyPortfolio() {
  return (
    <Scene>
      {(shadow) => (
        <>
          <path
            d="M90 80a8 8 0 0 1 8-8h62l16 18h126a8 8 0 0 1 8 8v142a8 8 0 0 1-8 8H98a8 8 0 0 1-8-8z"
            fill="var(--t2)"
            stroke="var(--ink)"
            strokeWidth="1.6"
            strokeLinejoin="round"
            filter={shadow}
          />
          <rect x="140" y="64" width="120" height="150" rx="5" fill="none" stroke="var(--ink3)" strokeOpacity="0.6" strokeWidth="1.6" strokeDasharray="5 6" />
          <path d="M156 92h70M156 108h86M156 124h56" stroke="var(--ink3)" strokeOpacity="0.3" strokeWidth="4" strokeLinecap="round" />
          <path
            d="M78 134a8 8 0 0 1 8-7h228a8 8 0 0 1 8 9l-12 106a8 8 0 0 1-8 7H98a8 8 0 0 1-8-7z"
            fill="var(--sheet)"
            stroke="var(--ink)"
            strokeWidth="1.6"
            strokeLinejoin="round"
            filter={shadow}
          />
        </>
      )}
    </Scene>
  )
}

export function Unreadable() {
  return (
    <Scene
      extraDefs={(id) => (
        <>
          <filter id={`${id}blur`}>
            <feGaussianBlur stdDeviation="3" />
          </filter>
          <clipPath id={`${id}lens`}>
            <circle cx="232" cy="150" r="46" />
          </clipPath>
        </>
      )}
    >
      {(shadow, id) => <UnreadableArt shadow={shadow} id={id} />}
    </Scene>
  )
}

function UnreadableArt({ shadow, id }: { shadow: string; id: string }) {
  return (
    <g transform="translate(-14 0)">
      <rect x="110" y="34" width="170" height="226" rx="6" fill="var(--sheet)" stroke="var(--ink)" strokeWidth="1.6" filter={shadow} />
      <path d="M130 64h100M130 82h120M130 100h80M130 190h120M130 208h96M130 226h110" stroke="var(--ink3)" strokeOpacity="0.45" strokeWidth="5" strokeLinecap="round" />
      <path d="M132 146c20-6 40 8 64-2s40 6 70-2" stroke="var(--ink3)" strokeOpacity="0.5" strokeWidth="12" strokeLinecap="round" fill="none" filter={`url(#${id}blur)`} />
      <circle cx="232" cy="150" r="46" fill="var(--paper)" />
      <g clipPath={`url(#${id}lens)`}>
        <path d="M150 142c26-10 52 12 84-2s52 8 90-2" stroke="var(--ink3)" strokeOpacity="0.45" strokeWidth="20" strokeLinecap="round" fill="none" filter={`url(#${id}blur)`} />
      </g>
      <circle cx="232" cy="150" r="48" fill="none" stroke="var(--ink)" strokeWidth="3" />
      <path d="M266 184l34 34" stroke="var(--ink)" strokeWidth="10" strokeLinecap="round" />
    </g>
  )
}

const CALENDAR_DAYS = 30

export function Calendar() {
  return (
    <Scene>
      {(shadow) => (
        <>
          <rect x="100" y="44" width="200" height="214" rx="8" fill="var(--sheet)" filter={shadow} />
          <path d="M100 84V52a8 8 0 0 1 8-8h184a8 8 0 0 1 8 8v32z" fill="var(--t4)" />
          <path d="M100 84h200" stroke="var(--ink)" strokeWidth="1.6" />
          <rect x="100" y="44" width="200" height="214" rx="8" fill="none" stroke="var(--ink)" strokeWidth="1.6" />
          <path d="M150 34v22M250 34v22" stroke="var(--ink)" strokeWidth="5" strokeLinecap="round" />
          <g fill="var(--ink3)" fillOpacity="0.28">
            {Array.from({ length: CALENDAR_DAYS }, (_, day) => (
              <rect key={day} x={119 + 24 * (day % 7)} y={110 + 26 * Math.floor(day / 7)} width="18" height="18" rx="3" />
            ))}
          </g>
          <rect x="164" y="211" width="24" height="24" rx="4" fill="var(--ink)" />
          <text x="176" y="228" textAnchor="middle" fontFamily="Newsreader, Georgia, serif" fontSize="13" fontWeight="600" fill="var(--onink)">
            31
          </text>
          <path d="M266 44v54l8-7 8 7V44z" fill="var(--ink)" stroke="var(--ink)" strokeWidth="1.6" strokeLinejoin="round" />
        </>
      )}
    </Scene>
  )
}
