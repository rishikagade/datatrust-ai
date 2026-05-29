import React, { useState } from 'react'
import { api } from '../api/client'
import { AuditResult } from '../types/audit'

const downloadFile = (content: string | Blob, fileName: string, type?: string) => {
  const blob = content instanceof Blob ? content : new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = fileName
  anchor.click()
  URL.revokeObjectURL(url)
}

const csvEscape = (value: unknown) => `"${String(value ?? '').replace(/"/g, '""')}"`

export default function DownloadReportPanel({ result }: { result: AuditResult }) {
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'failed'>('idle')
  const [pdfBusy, setPdfBusy] = useState(false)
  const [pdfError, setPdfError] = useState(false)

  const exportIssues = () => {
    const header = ['rule_id', 'rule_name', 'category', 'severity', 'affected_columns', 'affected_count', 'affected_pct', 'suggested_fix']
    const rows = result.rule_results?.map((rule) => [rule.rule_id, rule.rule_name, rule.category, rule.severity, rule.affected_columns?.join('; '), rule.affected_count, rule.affected_pct, rule.suggested_fix]) || []
    downloadFile([header, ...rows].map((row) => row.map(csvEscape).join(',')).join('\n'), `audit-${result.audit_id}-issues.csv`, 'text/csv')
  }

  const exportColumns = () => {
    const header = ['column', 'type', 'null_count', 'null_pct', 'unique_count']
    const rows = Object.entries(result.profile_stats || {}).map(([column, stats]: any) => [column, stats.inferred_type, stats.null_count, stats.null_pct, stats.unique_count])
    downloadFile([header, ...rows].map((row) => row.map(csvEscape).join(',')).join('\n'), `audit-${result.audit_id}-columns.csv`, 'text/csv')
  }

  const copyJson = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(result, null, 2))
      setCopyState('copied')
    } catch {
      setCopyState('failed')
    }
  }

  const downloadPdf = async () => {
    setPdfBusy(true)
    setPdfError(false)
    try {
      downloadFile(await api.pdfReport(result), `datatrust-${result.dataset.filename}.pdf`)
    } catch {
      setPdfError(true)
    } finally {
      setPdfBusy(false)
    }
  }

  return (
    <section className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
      <h2 className="font-semibold text-slate-950">Download and export</h2>
      <p className="mt-2 text-sm leading-6 text-slate-600">Export the audit report and reusable aggregate artifacts. None of these actions modifies the source dataset.</p>
      <div className="mt-5 grid gap-3 md:grid-cols-2">
        <button className="rounded-md bg-teal-700 px-4 py-3 text-left text-sm font-semibold text-white hover:bg-teal-800" disabled={pdfBusy} onClick={downloadPdf}>{pdfBusy ? 'Generating PDF...' : 'Download PDF report'}<span className="block text-xs font-normal text-teal-50">Best for stakeholder sharing</span></button>
        <button className="rounded-md bg-slate-900 px-4 py-3 text-left text-sm font-semibold text-white hover:bg-slate-800" onClick={exportIssues}>Download issues CSV<span className="block text-xs font-normal text-slate-200">Best for cleanup tracking</span></button>
        <button className="rounded-md border border-stone-300 bg-white px-4 py-3 text-left text-sm font-semibold text-slate-900 hover:bg-stone-50" onClick={exportColumns}>Download column statistics CSV<span className="block text-xs font-normal text-slate-500">Best for profiling and BI docs</span></button>
        <button className="rounded-md border border-stone-300 bg-white px-4 py-3 text-left text-sm font-semibold text-slate-900 hover:bg-stone-50" onClick={copyJson}>{copyState === 'copied' ? 'Copied' : copyState === 'failed' ? 'Copy failed' : 'Copy audit JSON'}<span className="block text-xs font-normal text-slate-500">Best for debugging or archiving</span></button>
      </div>
      {pdfError ? <p className="mt-3 text-sm font-medium text-red-700">PDF generation failed. Retry from this page.</p> : null}
    </section>
  )
}
