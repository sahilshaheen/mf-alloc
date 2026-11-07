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
