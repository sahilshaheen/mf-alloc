import { Route, Routes } from 'react-router'
import { Header } from './components/Header'
import { Screen } from './screens/Screen'

export default function App() {
  return (
    <>
      <Header />
      <Routes>
        <Route path="/" element={<Screen title="nav.overview" />} />
        <Route path="/asset-classes" element={<Screen title="nav.assetClasses" />} />
        <Route path="/funds" element={<Screen title="nav.funds" />} />
        <Route path="/data-and-method" element={<Screen title="nav.dataMethod" />} />
        <Route path="/privacy" element={<Screen title="nav.privacy" />} />
      </Routes>
    </>
  )
}
