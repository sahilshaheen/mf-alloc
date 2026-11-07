import { Route, Routes } from 'react-router'
import { Header } from './components/Header'
import { DataMethod } from './screens/DataMethod'
import { Overview } from './screens/Overview'
import { Screen } from './screens/Screen'
import { Welcome } from './screens/Welcome'

export default function App() {
  return (
    <>
      <Header />
      <Routes>
        <Route path="/welcome" element={<Welcome />} />
        <Route path="/" element={<Overview />} />
        <Route path="/asset-classes" element={<Screen title="nav.assetClasses" />} />
        <Route path="/funds" element={<Screen title="nav.funds" />} />
        <Route path="/data-and-method" element={<DataMethod />} />
        <Route path="/privacy" element={<Screen title="nav.privacy" />} />
      </Routes>
    </>
  )
}
