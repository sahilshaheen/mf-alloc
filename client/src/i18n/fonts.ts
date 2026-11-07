import type { Language } from './translator'

const latin = () => Promise.all([import('@fontsource-variable/newsreader'), import('@fontsource-variable/hanken-grotesk')])

const scripts: Record<Language, () => Promise<unknown>> = {
  en: async () => {},
  hi: () =>
    Promise.all([
      import('@fontsource/tiro-devanagari-hindi/400.css'),
      import('@fontsource/noto-sans-devanagari/400.css'),
      import('@fontsource/noto-sans-devanagari/500.css'),
      import('@fontsource/noto-sans-devanagari/600.css'),
    ]),
  ml: () =>
    Promise.all([
      import('@fontsource/noto-serif-malayalam/400.css'),
      import('@fontsource/noto-serif-malayalam/500.css'),
      import('@fontsource/noto-sans-malayalam/400.css'),
      import('@fontsource/noto-sans-malayalam/500.css'),
      import('@fontsource/noto-sans-malayalam/600.css'),
    ]),
}

export function loadFonts(language: Language): Promise<unknown> {
  return Promise.all([latin(), scripts[language]()])
}
