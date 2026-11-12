import { Navigate, Route, Routes } from 'react-router'
import { Header } from './components/Header'
import { Allocation } from './screens/Allocation'
import { DataMethod } from './screens/DataMethod'
import { Funds } from './screens/Funds'
import { Overview } from './screens/Overview'
import { Privacy } from './screens/Privacy'
import { Save } from './screens/Save'
import { Guide } from './screens/Guide'
import { Welcome } from './screens/Welcome'

export default function App() {
  return (
    <>
      <Header />
      <Routes>
        <Route path="/welcome" element={<Welcome />} />
        <Route path="/" element={<Overview />} />
        <Route path="/allocation/:bucket?" element={<Allocation />} />
        <Route path="/funds/:isin?" element={<Funds />} />
        <Route path="/returns" element={<Navigate to="/funds?view=returns" replace />} />
        <Route path="/data-and-method" element={<DataMethod />} />
        <Route path="/privacy" element={<Privacy />} />
        <Route path="/get-statement" element={<Guide />} />
        <Route path="/save" element={<Save />} />
      </Routes>
    </>
  )
}
