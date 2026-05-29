import React from 'react'
import { ScoreBreakdownItem } from '../types/audit'

type Props = { items: ScoreBreakdownItem[]; totalDeduction?: number; overallScore?: number }

const descriptions: Record<string, string> = {
  missing_value: 'Completeness penalty based on the most affected column.',
  duplicate_rows: 'Exact duplicate rows that can inflate counts and aggregations.',
  invalid_type: 'Invalid values and mixed date formats that can break transformations.',
  outliers: 'Statistically extreme numeric values that may need review.',
  critical_failures: 'Critical rule findings that create trust or integrity risk.',
  business_rule_violations: 'Domain checks such as ranges, date ordering, freshness, and category consistency.',
}

export default function ScoreBreakdownPanel({ items, totalDeduction, overallScore }: Props) {
  if (!items.length) return null
  return (
    <section className="mt-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="font-semibold text-slate-950">Score breakdown</h2>
      <p className="mt-2 text-sm leading-6 text-slate-600">Each category shows its weighted contribution to the total score deduction.</p>
      {totalDeduction !== undefined && overallScore !== undefined ? (
        <p className="mt-3 text-sm font-semibold text-slate-800">Total deduction: -{Number(totalDeduction).toFixed(1)} points. Final score: {Math.round(overallScore)} / 100.</p>
      ) : null}
      <div className="mt-4 grid gap-3">
        {items.map((item) => (
          <article key={item.key} className="rounded-md border border-slate-200 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="font-semibold text-slate-950">{item.label}</h3>
                <p className="mt-1 text-sm text-slate-600">{descriptions[item.key] || 'Weighted audit component.'}</p>
              </div>
              <div className="text-right">
                <div className="font-semibold text-slate-950">-{item.weightedImpact.toFixed(1)} pts</div>
                <div className="text-xs text-slate-500">{item.weight}% weight</div>
              </div>
            </div>
            <progress className="mt-3 h-2 w-full rounded-full accent-green-600" max={100} value={item.health} />
          </article>
        ))}
      </div>
    </section>
  )
}
