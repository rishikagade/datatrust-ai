import React from 'react'
import { Link, useParams } from 'react-router-dom'
import SeverityBadge from '../components/SeverityBadge'
import { useAuditResult } from '../hooks/useAuditResult'

export default function ColumnProfilePage() {
  const { columnName = '' } = useParams<{ columnName: string }>()
  const decoded = decodeURIComponent(columnName)
  const { result, loading, error } = useAuditResult()
  if (loading) return <main className="p-6"><div className="h-32 animate-pulse rounded-lg bg-stone-200" /></main>
  if (error || !result) return <main className="p-6 text-red-700">{error || 'No audit loaded.'}</main>
  const profile = result.profile_stats?.[decoded]
  const findings = (result.rule_results || []).filter((rule) => (rule.affected_columns || []).includes(decoded))
  const columns = Object.keys(result.profile_stats || {})
  const currentIndex = columns.indexOf(decoded)
  const previousColumn = currentIndex > 0 ? columns[currentIndex - 1] : null
  const nextColumn = currentIndex >= 0 && currentIndex < columns.length - 1 ? columns[currentIndex + 1] : null

  return (
    <main className="min-h-screen bg-stone-50 px-6 py-6">
      <div className="mx-auto max-w-5xl">
        <section className="rounded-lg border border-stone-200 bg-white p-6 shadow-sm">
          <Link className="text-sm font-semibold text-teal-700" to={`/audit/${result.audit_id}`}>Back to dashboard</Link>
          <h1 className="mt-3 text-3xl font-bold text-slate-950">{decoded}</h1>
          <p className="mt-2 text-slate-600">Column-level profile, distribution summary, and all findings connected to this field.</p>
          <div className="mt-5 flex flex-wrap gap-3">
            {previousColumn ? <Link className="rounded-md border border-stone-300 px-3 py-2 text-sm font-semibold hover:bg-stone-50" to={`/audit/${result.audit_id}/column/${encodeURIComponent(previousColumn)}`}>Previous: {previousColumn}</Link> : null}
            {nextColumn ? <Link className="rounded-md border border-stone-300 px-3 py-2 text-sm font-semibold hover:bg-stone-50" to={`/audit/${result.audit_id}/column/${encodeURIComponent(nextColumn)}`}>Next: {nextColumn}</Link> : null}
          </div>
        </section>
        {!profile ? <p className="mt-5 rounded-md border border-stone-200 bg-white p-5 text-slate-600">No profile exists for this column.</p> : (
          <section className="mt-5 rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
            <div className="grid gap-4 md:grid-cols-4">
              <div><p className="text-sm text-slate-500">Type</p><p className="mt-1 font-semibold">{profile.inferred_type}</p></div>
              <div><p className="text-sm text-slate-500">Null rate</p><p className="mt-1 font-semibold">{Number(profile.null_pct || 0).toFixed(1)}%</p></div>
              <div><p className="text-sm text-slate-500">Null count</p><p className="mt-1 font-semibold">{profile.null_count}</p></div>
              <div><p className="text-sm text-slate-500">Unique count</p><p className="mt-1 font-semibold">{profile.unique_count}</p></div>
            </div>
            {profile.numeric_summary ? (
              <div className="mt-6">
                <h2 className="font-semibold text-slate-950">Numeric summary</h2>
                <div className="mt-3 grid gap-3 md:grid-cols-3">{Object.entries(profile.numeric_summary).map(([key, value]) => <div key={key} className="rounded-md bg-stone-50 p-3 text-sm"><span className="font-semibold">{key}</span>: {String(value)}</div>)}</div>
              </div>
            ) : (
              <div className="mt-6">
                <h2 className="font-semibold text-slate-950">Top values</h2>
                <div className="mt-3 grid gap-2">{(profile.top_values || []).slice(0, 5).map((item: any) => <div key={item.value} className="rounded-md bg-stone-50 p-3 text-sm">{item.value}: {item.count} rows ({item.pct}%)</div>)}</div>
              </div>
            )}
          </section>
        )}
        <section className="mt-6 rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
          <h2 className="font-semibold text-slate-950">Findings affecting this column</h2>
          <div className="mt-4 grid gap-3">
            {findings.length ? findings.map((rule) => <article key={`${rule.rule_id}-${rule.description}`} className="rounded-md border border-stone-200 bg-stone-50 p-4"><div className="flex justify-between gap-3"><h3 className="font-semibold">{rule.rule_name}</h3><SeverityBadge severity={rule.severity} /></div><p className="mt-2 text-sm leading-6 text-slate-600">{rule.description}</p></article>) : <p className="text-sm text-slate-500">No findings affect this column.</p>}
          </div>
        </section>
      </div>
    </main>
  )
}
