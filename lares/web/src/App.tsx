import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import MapPage from './pages/MapPage'
import InfrastructureDirectoryPage from './pages/InfrastructureDirectoryPage'
import InfrastructureDetailPage from './pages/InfrastructureDetailPage'
import OrganisationDetailPage from './pages/OrganisationDetailPage'
import OrganisationDirectoryPage from './pages/OrganisationDirectoryPage'
import SearchPage from './pages/SearchPage'
import CoveragePage from './pages/CoveragePage'
import SourcesPage from './pages/SourcesPage'
import ReviewQueuePage from './pages/ReviewQueuePage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/map" replace />} />
        <Route path="/map" element={<MapPage />} />
        <Route path="/infrastructure" element={<InfrastructureDirectoryPage />} />
        <Route path="/infrastructure/:id" element={<InfrastructureDetailPage />} />
        <Route path="/organisations" element={<OrganisationDirectoryPage />} />
        <Route path="/organisations/:id" element={<OrganisationDetailPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/coverage" element={<CoveragePage />} />
        <Route path="/sources" element={<SourcesPage />} />
        <Route path="/review-queue" element={<ReviewQueuePage />} />
      </Route>
    </Routes>
  )
}
