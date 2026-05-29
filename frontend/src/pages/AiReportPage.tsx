import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useAuditResult } from '../hooks/useAuditResult'
import { makeMarkdownReport } from '../utils/audit'

export default function AiReportPage() {
  const { result, loading, error } = useAuditResult()
  const [copied, setCopied] = useState(false)
  const [pdfBusy, setPdfBusy] = useState(false)
  if (loading) return <main className="p-6"><div className="h-32 animate-pulse rounded-lg bg-stone-200" /></main>
  if (error || !result) return <main className="p-6 text-red-700">{error || 'No audit loaded.'}</main>
  const report = result.ai_report

  const copyMarkdown = async () => {
    await navigator.clipboard.writeText(makeMarkdownReport(result))
    setCopied(true)
  }

  const downloadPdf = async () => {
    setPdfBusy(true)
    try {
      const blob = await api.pdfReport(result)
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = `datatrust-${result.dataset.filename}.pdf`
      anchor.click()
      URL.revokeObjectURL(url)
    } finally {
      setPdfBusy(false)
    }
  }

  return (
    <main className="min-h-screen bg-stone-50 px-6 py-6">
      <article className="mx-auto max-w-4xl rounded-lg border border-stone-200 bg-white p-8 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <Link className="text-sm font-semibold text-teal-700" to={`/audit/${result.audit_id}`}>Back to dashboard</Link>
            <h1 className="mt-3 text-3xl font-bold text-slate-950">AI audit report</h1>
            <p className="mt-2 text-slate-600">{result.dataset.filename}</p>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">A business-readable version of the deterministic audit findings, written from sanitized aggregate statistics only.</p>
            <p className="mt-3 max-w-2xl rounded-md border border-teal-200 bg-teal-50 p-3 text-sm leading-6 text-teal-950">Privacy note: this report is generated from aggregate rule findings only. Raw CSV rows and individual cell values are not sent to the AI model.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button className="rounded-md bg-teal-700 px-4 py-2 text-sm font-semibold text-white" disabled={pdfBusy} onClick={downloadPdf}>{pdfBusy ? 'Preparing...' : 'Download PDF'}</button>
            <button className="rounded-md border border-stone-300 px-4 py-2 text-sm font-semibold hover:bg-stone-50" onClick={copyMarkdown}>{copied ? 'Copied' : 'Copy as Markdown'}</button>
          </div>
        </div>
        {[
          ['Executive Summary', report?.executive_summary],
          ['Risk Interpretation', report?.risk_interpretation],
          ['Cleaning Recommendations', report?.cleaning_recommendations],
          ['Dashboard And Model Impact', report?.dashboard_impact],
        ].map(([title, text]) => (
          <section key={title} className="mt-8 border-t border-stone-200 pt-6">
            <h2 className="text-xl font-semibold text-slate-950">{title}</h2>
            <p className="mt-3 leading-7 text-slate-700">{text || 'This section is not available.'}</p>
          </section>
        ))}
      </article>
    </main>
  )
}
