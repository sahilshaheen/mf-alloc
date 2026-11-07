const dark = window.matchMedia('(prefers-color-scheme: dark)')

function applySystemTheme(): void {
  document.documentElement.dataset.theme = dark.matches ? 'dark' : 'light'
}

export function followSystemTheme(): void {
  applySystemTheme()
  dark.addEventListener('change', applySystemTheme)
}
