const AMC_NAMES: Record<string, string> = {
  absl: 'Aditya Birla Sun Life',
  dsp: 'DSP',
  hdfc: 'HDFC',
  icici: 'ICICI Prudential',
  kotak: 'Kotak',
  mirae: 'Mirae Asset',
  motilal: 'Motilal Oswal',
  nippon: 'Nippon India',
  ppfas: 'PPFAS (Parag Parikh)',
  sbi: 'SBI',
  tata: 'Tata',
  uti: 'UTI',
  wealth: 'The Wealth Company',
}

export const amcName = (code: string): string => AMC_NAMES[code] ?? code.toUpperCase()

interface AmcLogo {
  file: string
  onDark?: boolean
}

const AMC_LOGOS: Record<string, AmcLogo> = {
  absl: { file: 'absl.webp' },
  dsp: { file: 'dsp.svg' },
  hdfc: { file: 'hdfc.svg' },
  icici: { file: 'icici.svg' },
  kotak: { file: 'kotak.png' },
  mirae: { file: 'mirae.jpg' },
  motilal: { file: 'motilal.png', onDark: true },
  nippon: { file: 'nippon.png' },
  ppfas: { file: 'ppfas.jpg' },
  sbi: { file: 'sbi.svg' },
  tata: { file: 'tata.avif' },
  uti: { file: 'uti.webp' },
  wealth: { file: 'wealth.svg' },
}

export const amcLogo = (code: string): AmcLogo | undefined => AMC_LOGOS[code]
