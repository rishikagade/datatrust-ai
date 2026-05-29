import React, { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import SeverityBadge from '../components/SeverityBadge'
import { useAuditResult } from '../hooks/useAuditResult'
import { sortedRules } from '../utils/audit'

export default function IssueListPage() {
  const { result, loading, error } = useAuditResult()
  const [severity, setSeverity] = useState('All')
  const [category, setCategory] = useState('All')
  const [open, setOpen] = useState<string | null>(null)
  const rules = sortedRules(result?.rule_results || [])
  const categories = useMemo(() => ['All', ...Array.from(new Set(rules.map((rule) => rule.category || 'Other')))], [rules])
  const filtered = rules.filter((rule) => (severity === 'All' || rule.severity === severity) && (category === 'All' || (rule.category || 'Other') === category))

  if (loading) return <main className="p-6"><div className="h-32 animate-pulse rounded-lg bg-stone-200" /></main>
  if (error || !result) return <main className="p-6 text-red-700">{error || 'No audit loaded.'}</main>

  return (
    <main className="min-h-screen bg-stone-50 px-6 py-6">
      <div className="mx-auto max-w-5xl">
        <section className="rounded-lg border border-stone-200 bg-white p-6 shadow-sm">
          <Link className="text-sm font-semibold text-teal-700" to={`/audit/${result.audit_id}`}>Back to dashboard</Link>
          <h1 className="mt-3 text-3xl font-bold text-slate-950">Issue list</h1>
          <p className="mt-2 max-w-2xl text-slate-600">Filter the findings, expand an issue, and use the suggested fix as your cleanup starting point.</p>
        </section>
        <div className="mt-5 flex flex-wrap gap-3 rounded-lg border border-stone-200 bg-white p-4 shadow-sm">
          <select className="rounded-md border border-stone-300 bg-white px-3 py-2 text-sm" value={severity} onChange={(event) => setSeverity(event.target.value)}>
            {['All', 'Critical', 'High', 'Medium', 'Low'].map((value) => <option key={value}>{value}</option>)}
          </select>
          <select className="rounded-md border border-stone-300 bg-white px-3 py-2 text-sm" value={category} onChange={(event) => setCategory(event.target.value)}>
            {categories.map((value) => <option key={value}>{value}</option>)}
          </select>
        </div>
        <div className="mt-5 grid gap-3">
          {filtered.length ? filtered.map((rule, index) => {
            const key = `${rule.rule_id}-${index}`
            return (
              <article key={key} className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
                <button className="flex w-full items-start justify-between gap-4 text-left" onClick={() => setOpen(open === key ? null : key)}>
                  <span>
                    <span className="block font-semibold text-slate-950">{rule.rule_name}</span>
                    <span className="mt-1 block text-sm text-slate-600">{rule.affected_count} rows • {rule.affected_pct}% affected • {(rule.affected_columns || []).join(', ') || 'dataset level'}</span>
                  </span>
                  <SeverityBadge severity={rule.severity} />
                </button>
                {open === key ? <div className="mt-4 rounded-md bg-stone-50 p-4 text-sm leading-6 text-slate-700"><p>{rule.description}</p><p className="mt-2 font-semibold">Suggested fix: {rule.suggested_fix}</p></div> : null}
              </article>
            )
          }) : <p className="rounded-md border border-stone-200 bg-white p-5 text-sm text-slate-500">No findings match the selected filters.</p>}
        </div>
      </div>
    </main>
  )
}
