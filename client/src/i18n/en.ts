export const en = {
  'nav.label': 'Main',
  'nav.overview': 'Overview',
  'nav.assetClasses': 'Asset classes',
  'nav.funds': 'Funds',
  'nav.dataMethod': 'Data and method',
  'nav.privacy': 'Privacy',
  'header.search': 'Search',
  'header.onDevice': 'On this device',
  'header.language': 'Language',
  'overview.matched': '{pct} of value matched.',
} as const

export type Dictionary = Record<keyof typeof en, string>
