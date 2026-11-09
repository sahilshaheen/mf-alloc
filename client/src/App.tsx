import { Route, Routes } from 'react-router'
import { Header } from './components/Header'
import { Breakdowns } from './screens/Breakdowns'
import { DataMethod } from './screens/DataMethod'
import { Funds } from './screens/Funds'
import { Overview } from './screens/Overview'
import { Privacy } from './screens/Privacy'
import { Returns } from './screens/Returns'
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
        <Route path="/breakdowns/:bucket?" element={<Breakdowns />} />
        <Route path="/funds/:isin?" element={<Funds />} />
        <Route path="/returns" element={<Returns />} />
        <Route path="/data-and-method" element={<DataMethod />} />
        <Route path="/privacy" element={<Privacy />} />
        <Route path="/get-statement" element={<Guide />} />
        <Route path="/save" element={<Save />} />
      </Routes>
    </>
  )
}
