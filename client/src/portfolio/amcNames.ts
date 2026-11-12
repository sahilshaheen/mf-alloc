const AMC_NAMES: Record<string, string> = {
  absl: 'Aditya Birla Sun Life',
  axis: 'Axis',
  dsp: 'DSP',
  hdfc: 'HDFC',
  icici: 'ICICI Prudential',
  iti: 'ITI',
  kotak: 'Kotak',
  mahindra: 'Mahindra Manulife',
  mirae: 'Mirae Asset',
  motilal: 'Motilal Oswal',
  nippon: 'Nippon India',
  ppfas: 'PPFAS (Parag Parikh)',
  quant: 'quant',
  sbi: 'SBI',
  tata: 'Tata',
  union: 'Union',
  uti: 'UTI',
  wealth: 'The Wealth Company',
  whiteoak: 'WhiteOak Capital',
}

export const amcName = (code: string): string => AMC_NAMES[code] ?? code.toUpperCase()

interface AmcLogo {
  file: string
  onDark?: boolean
}

const AMC_LOGOS: Record<string, AmcLogo> = {
  absl: { file: 'absl.webp' },
  axis: { file: 'axis.svg', onDark: true },
  dsp: { file: 'dsp.svg' },
  hdfc: { file: 'hdfc.svg' },
  icici: { file: 'icici.svg' },
  iti: { file: 'iti.jpeg' },
  kotak: { file: 'kotak.png' },
  mahindra: { file: 'mahindra.svg' },
  mirae: { file: 'mirae.jpg' },
  motilal: { file: 'motilal.png', onDark: true },
  nippon: { file: 'nippon.png' },
  ppfas: { file: 'ppfas.jpg' },
  quant: { file: 'quant.png' },
  sbi: { file: 'sbi.svg' },
  tata: { file: 'tata.avif' },
  union: { file: 'union.png' },
  uti: { file: 'uti.webp' },
  wealth: { file: 'wealth.svg' },
  whiteoak: { file: 'whiteoak.png' },
}

export const amcLogo = (code: string): AmcLogo | undefined => AMC_LOGOS[code]
