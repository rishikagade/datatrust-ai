import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import UploadPage from './pages/UploadPage'
import AuditDashboard from './pages/AuditDashboard'
import AiAgentPage from './pages/AiAgentPage'
import ColumnProfilePage from './pages/ColumnProfilePage'
import IssueListPage from './pages/IssueListPage'
import AiReportPage from './pages/AiReportPage'
import DownloadPage from './pages/DownloadPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/audit/:auditId" element={<AuditDashboard />} />
        <Route path="/audit/:auditId/column/:columnName" element={<ColumnProfilePage />} />
        <Route path="/audit/:auditId/issues" element={<IssueListPage />} />
        <Route path="/audit/:auditId/report" element={<AiReportPage />} />
        <Route path="/audit/:auditId/download" element={<DownloadPage />} />
        <Route path="/audit/:auditId/assistant" element={<AiAgentPage />} />
      </Routes>
    </BrowserRouter>
  )
}
