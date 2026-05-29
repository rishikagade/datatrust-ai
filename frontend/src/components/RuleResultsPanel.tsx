import React from 'react'
import { RuleResult } from '../types/audit'
import SeverityBadge from './SeverityBadge'

export default function RuleResultsPanel({ rulesByCategory }: { rulesByCategory: Record<string, RuleResult[]> }) {
  const groups = Object.entries(rulesByCategory)
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="font-semibold text-slate-950">Rule findings</h2>
      <div className="mt-4 grid gap-4">
        {groups.length ? groups.map(([category, rules]) => (
          <div key={category}>
            <h3 className="text-sm font-bold uppercase tracking-wide text-slate-500">{category}</h3>
            <div className="mt-2 grid gap-2">
              {rules.map((rule) => <article key={`${rule.rule_id}-${rule.description}`} className="rounded-md border border-slate-200 p-3"><div className="flex justify-between gap-3"><span className="font-semibold">{rule.rule_name}</span><SeverityBadge severity={rule.severity} /></div><p className="mt-2 text-sm text-slate-600">{rule.description}</p></article>)}
            </div>
          </div>
        )) : <p className="text-sm text-slate-500">No rule findings are available.</p>}
      </div>
    </section>
  )
}
