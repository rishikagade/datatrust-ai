import React from 'react'
import { AiReport } from '../types/audit'

export default function AiSummaryPanel({ report }: { report: AiReport }) {
  return (
    <section className="rounded-lg border border-blue-200 bg-blue-50 p-5">
      <h2 className="font-semibold text-blue-950">AI audit summary</h2>
      <p className="mt-3 text-sm leading-6 text-blue-950">{report.executive_summary}</p>
    </section>
  )
}
