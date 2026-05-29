import React from 'react'
import { Link } from 'react-router-dom'
import DownloadReportPanel from '../components/DownloadReportPanel'
import { useAuditResult } from '../hooks/useAuditResult'

export default function DownloadPage() {
  const { result, loading, error } = useAuditResult()
  if (loading) return <main className="p-6"><div className="h-32 animate-pulse rounded-lg bg-stone-200" /></main>
  if (error || !result) return <main className="p-6 text-red-700">{error || 'No audit loaded.'}</main>
  return (
    <main className="min-h-screen bg-stone-50 px-6 py-6">
      <div className="mx-auto max-w-5xl">
        <section className="rounded-lg border border-stone-200 bg-white p-6 shadow-sm">
          <Link className="text-sm font-semibold text-teal-700" to={`/audit/${result.audit_id}`}>Back to dashboard</Link>
          <h1 className="mt-3 text-3xl font-bold text-slate-950">Download audit</h1>
          <p className="mt-2 max-w-2xl text-slate-600">Choose the format that fits your next step: stakeholder report, issue queue, column profile export, or full audit JSON.</p>
        </section>
        <div className="mt-6"><DownloadReportPanel result={result} /></div>
      </div>
    </main>
  )
}
