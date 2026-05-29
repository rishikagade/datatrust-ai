import React from 'react'
import { AuditResult } from '../types/audit'
import { scoreTier } from '../utils/audit'

export default function AuditHeader({ result, score }: { result: AuditResult; score?: number }) {
  const tier = scoreTier(score)
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="font-semibold text-slate-950">Audit summary</h2>
        <p className="mt-3 text-sm text-slate-600">{result.dataset.filename}</p>
        <p className="mt-1 text-sm text-slate-600">{result.dataset.row_count} rows • {result.dataset.column_count} columns</p>
      </section>
      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="font-semibold text-slate-950">Quality score</h2>
        <p className="mt-3 text-4xl font-bold text-slate-950">{score === undefined ? 'N/A' : Math.round(score)}</p>
        <p className="mt-2 text-sm font-semibold text-blue-700">{tier.label}</p>
      </section>
    </div>
  )
}
