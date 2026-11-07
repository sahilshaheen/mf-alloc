import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router'
import './styles/base.css'
import App from './App.tsx'
import { I18nProvider } from './i18n/I18nProvider'
import { PortfolioProvider } from './portfolio/PortfolioProvider'
import './statement/pdfWorker'
import { followSystemTheme } from './theme'

followSystemTheme()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <I18nProvider>
        <PortfolioProvider>
          <App />
        </PortfolioProvider>
      </I18nProvider>
    </BrowserRouter>
  </StrictMode>,
)
