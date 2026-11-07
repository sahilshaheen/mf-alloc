import { Route, Routes } from 'react-router'
import { Header } from './components/Header'
import { Breakdowns } from './screens/Breakdowns'
import { DataMethod } from './screens/DataMethod'
import { Funds } from './screens/Funds'
import { Overview } from './screens/Overview'
import { Privacy } from './screens/Privacy'
import { Welcome } from './screens/Welcome'

export default function App() {
  return (
    <>
      <Header />
      <Routes>
        <Route path="/welcome" element={<Welcome />} />
        <Route path="/" element={<Overview />} />
        <Route path="/breakdowns/:bucket?" element={<Breakdowns />} />
        <Route path="/funds/:isin?" element={<Funds />} />
        <Route path="/data-and-method" element={<DataMethod />} />
        <Route path="/privacy" element={<Privacy />} />
      </Routes>
    </>
  )
}
