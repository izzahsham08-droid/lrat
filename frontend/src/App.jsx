import { Routes, Route, Navigate } from 'react-router-dom'
import { AssessmentProvider } from './context/AssessmentContext'
import Layout from './components/Layout'
import Home from './pages/Home'
import BuildingPage from './pages/BuildingPage'
import LinesPage from './pages/LinesPage'
import ZonesPage from './pages/ZonesPage'
import ResultsPage from './pages/ResultsPage'

export default function App() {
  return (
    <AssessmentProvider>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="building" element={<BuildingPage />} />
          <Route path="lines" element={<LinesPage />} />
          <Route path="zones" element={<ZonesPage />} />
          <Route path="results" element={<ResultsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </AssessmentProvider>
  )
}
