import React, { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import AiAgentPage from './AiAgentPage'
import SeverityBadge from '../components/SeverityBadge'
import SeverityPieChart from '../components/SeverityPieChart'
import ScoreBreakdownPanel from '../components/ScoreBreakdownPanel'
import { useAuditResult } from '../hooks/useAuditResult'
import { columnIssueMap, completenessColor, scoreBreakdown, scoreTier, sortedRules, worstSeverity } from '../utils/audit'

export default function AuditDashboard() {
  const { auditId, result, loading, error } = useAuditResult()
  const navigate = useNavigate()
  const [agentOpen, setAgentOpen] = useState(false)
  const [sortKey, setSortKey] = useState<'risk' | 'name' | 'completeness' | 'issues'>('risk')

  const score = result?.scoring?.overall_score
  const tier = scoreTier(score)
  const issues = result?.rule_results || []
  const issueMap = columnIssueMap(result)
  const profileEntries = Object.entries(result?.profile_stats || {})
  const severityData = useMemo(() => {
    const counts: Record<string, number> = { Critical: 0, High: 0, Medium: 0, Low: 0 }
    issues.forEach((rule) => { counts[rule.severity] = (counts[rule.severity] || 0) + 1 })
    return Object.entries(counts).filter(([, value]) => value > 0).map(([name, value]) => ({ name, value }))
  }, [issues])
  const criticalCount = issues.filter((rule) => rule.severity === 'Critical').length
  const columnsWithIssues = Object.keys(issueMap).length
  const topIssues = sortedRules(issues).slice(0, 3)
  const firstColumn = profileEntries[0]?.[0] || ''
  const missingBars = profileEntries
    .map(([name, stats]: any) => {
      const missingRule = (issueMap[name] || []).find((rule) => rule.rule_id === 'missing_values')
      return { name, pct: Number(stats.null_pct || 0), severity: missingRule?.severity || 'Low' }
    })
    .filter((item) => item.pct > 0)
    .sort((a, b) => b.pct - a.pct)
  const rankedColumns = useMemo(() => {
    const rows = profileEntries.map(([name, stats]: any) => {
      const rules = issueMap[name] || []
      const completeness = 100 - Number(stats.null_pct || 0)
      return { name, stats, rules, completeness, severity: worstSeverity(rules) }
    })
    return rows.sort((a, b) => {
      if (sortKey === 'name') return a.name.localeCompare(b.name)
      if (sortKey === 'completeness') return a.completeness - b.completeness
      if (sortKey === 'issues') return b.rules.length - a.rules.length
      const severityOrder: Record<string, number> = { Critical: 0, High: 1, Medium: 2, Low: 3 }
      return (severityOrder[a.severity] ?? 3) - (severityOrder[b.severity] ?? 3) || b.rules.length - a.rules.length || a.completeness - b.completeness
    })
  }, [issueMap, profileEntries, sortKey])
  const demoDataset = result?.metadata?.demo_dataset
  const missingAccent: Record<string, string> = {
    Critical: 'accent-red-600',
    High: 'accent-orange-600',
    Medium: 'accent-amber-500',
    Low: 'accent-green-600',
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-stone-50 p-6">
        <div className="mx-auto max-w-7xl">
          <div className="h-40 animate-pulse rounded-lg bg-white shadow-sm" />
          <div className="mt-5 grid gap-4 md:grid-cols-4">
            {[1, 2, 3, 4].map((item) => <div key={item} className="h-32 animate-pulse rounded-lg bg-white shadow-sm" />)}
          </div>
        </div>
      </main>
    )
  }
  if (error || !result) {
    return (
      <main className="min-h-screen bg-stone-50 p-6">
        <div className="mx-auto max-w-3xl rounded-lg border border-red-200 bg-white p-6 shadow-sm">
          <h1 className="text-xl font-bold text-slate-950">Audit not available</h1>
          <p className="mt-2 text-slate-600">{error || 'No audit is loaded.'}</p>
          <Link className="mt-5 inline-flex rounded-md bg-teal-700 px-4 py-2 text-sm font-semibold text-white" to="/upload">Upload or load a demo</Link>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-stone-50 px-6 py-6">
      <div className="mx-auto max-w-7xl">
        <header className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
          {demoDataset ? <div className="mb-4 rounded-md border border-teal-200 bg-teal-50 px-4 py-3 text-sm font-semibold text-teal-900">Demo mode: this dashboard was generated from the live `{demoDataset}` sample dataset.</div> : null}
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <Link className="text-sm font-semibold text-teal-700" to="/">DataTrust AI</Link>
              <h1 className="mt-2 text-3xl font-bold text-slate-950">{result.dataset.filename}</h1>
              <p className="mt-2 text-sm text-slate-600">{result.dataset.row_count.toLocaleString()} rows • {result.dataset.column_count} columns • audit {auditId}</p>
            </div>
            <div className="flex flex-wrap gap-3">
              <button className="rounded-md bg-teal-700 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-teal-800" onClick={() => setAgentOpen(true)}>Ask AI Agent</button>
              <Link className="rounded-md border border-stone-300 bg-white px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-stone-50" to={`/audit/${result.audit_id}/download`}>Download</Link>
              <Link className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800" to="/upload">Upload another</Link>
            </div>
          </div>
          <nav className="mt-5 flex flex-wrap gap-2 border-t border-stone-100 pt-4">
            <span className="rounded-full bg-teal-50 px-3 py-1.5 text-sm font-semibold text-teal-800">Overview</span>
            <Link className="rounded-full px-3 py-1.5 text-sm font-semibold text-slate-600 hover:bg-stone-100" to={`/audit/${result.audit_id}/issues`}>Issues</Link>
            {firstColumn ? <Link className="rounded-full px-3 py-1.5 text-sm font-semibold text-slate-600 hover:bg-stone-100" to={`/audit/${result.audit_id}/column/${encodeURIComponent(firstColumn)}`}>Columns</Link> : null}
            <Link className="rounded-full px-3 py-1.5 text-sm font-semibold text-slate-600 hover:bg-stone-100" to={`/audit/${result.audit_id}/report`}>AI report</Link>
            <Link className="rounded-full px-3 py-1.5 text-sm font-semibold text-slate-600 hover:bg-stone-100" to={`/audit/${result.audit_id}/download`}>Exports</Link>
          </nav>
        </header>

        <section className="mt-6 grid gap-5 lg:grid-cols-[1.35fr_0.65fr]">
          <div className="rounded-lg border border-stone-200 bg-white p-6 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-5">
              <div>
                <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Quality score</h2>
                <div className="mt-3 flex items-end gap-3">
                  <span className="text-6xl font-bold text-slate-950">{Math.round(score || 0)}</span>
                  <span className="pb-2 text-lg font-semibold text-slate-500">/ 100</span>
                </div>
                <p className="mt-3 inline-flex rounded-full bg-teal-50 px-3 py-1 text-sm font-semibold text-teal-800">{tier.label}</p>
                <p className="mt-4 max-w-2xl text-base leading-7 text-slate-700">{tier.interpretation}</p>
              </div>
              <div className="w-full max-w-sm rounded-lg bg-stone-50 p-4">
                <h3 className="font-semibold text-slate-950">Recommended next step</h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  {topIssues[0] ? `Start with ${topIssues[0].rule_name.toLowerCase()}${topIssues[0].affected_columns?.length ? ` in ${topIssues[0].affected_columns.join(', ')}` : ''}.` : 'No issues were detected. Review the AI report and export the audit if needed.'}
                </p>
                {topIssues[0] ? <Link className="mt-4 inline-flex text-sm font-semibold text-teal-700" to={`/audit/${result.audit_id}/issues`}>Review prioritized issues</Link> : null}
              </div>
            </div>
          </div>
          <div>
            <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
              <div className="rounded-lg border border-stone-200 bg-white p-4 shadow-sm">
                <p className="text-sm font-semibold text-slate-500">Rows</p>
                <p className="mt-2 text-2xl font-bold text-slate-950">{result.dataset.row_count.toLocaleString()}</p>
                {result.dataset.row_count < 100 ? <p className="mt-1 text-xs font-semibold text-orange-700">Small dataset warning</p> : <p className="mt-1 text-xs text-slate-500">Enough volume for a directional audit.</p>}
              </div>
              <div className="rounded-lg border border-stone-200 bg-white p-4 shadow-sm">
                <p className="text-sm font-semibold text-slate-500">Columns</p>
                <p className="mt-2 text-2xl font-bold text-slate-950">{result.dataset.column_count}</p>
                <p className="mt-1 text-xs text-slate-500">{columnsWithIssues} with findings</p>
              </div>
              <div className={`rounded-lg border p-4 shadow-sm ${criticalCount ? 'border-red-200 bg-red-50' : 'border-stone-200 bg-white'}`}>
                <p className="text-sm font-semibold text-slate-500">Critical</p>
                <p className={`mt-2 text-2xl font-bold ${criticalCount ? 'text-red-700' : 'text-slate-950'}`}>{criticalCount}</p>
                <p className="mt-1 text-xs text-slate-500">{criticalCount ? 'Fix these first.' : 'No critical findings.'}</p>
              </div>
            </div>
          </div>
        </section>

        <section className="mt-6 grid gap-5 lg:grid-cols-[0.8fr_1.2fr]">
          <SeverityPieChart data={severityData} />
          <div className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between gap-4">
              <h2 className="font-semibold text-slate-950">AI executive summary</h2>
              <Link className="text-sm font-semibold text-teal-700" to={`/audit/${result.audit_id}/report`}>Full report</Link>
            </div>
            <p className="mt-4 leading-7 text-slate-700">{result.ai_report?.executive_summary || 'AI summary is not available for this audit.'}</p>
            <div className="mt-5 flex flex-wrap gap-3">
              <button className="rounded-md border border-teal-200 bg-teal-50 px-4 py-2 text-sm font-semibold text-teal-800 hover:bg-teal-100" onClick={() => setAgentOpen(true)}>Ask a follow-up</button>
              <Link className="rounded-md border border-stone-300 bg-white px-4 py-2 text-sm font-semibold text-slate-800 hover:bg-stone-50" to={`/audit/${result.audit_id}/report`}>Read full narrative</Link>
            </div>
          </div>
        </section>

        <section className="mt-6 grid gap-5 lg:grid-cols-2">
          <div className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="font-semibold text-slate-950">Completeness watchlist</h2>
                <p className="mt-1 text-sm text-slate-500">Columns with missing values, sorted by impact.</p>
              </div>
              <Link className="text-sm font-semibold text-teal-700" to={`/audit/${result.audit_id}/issues`}>All issues</Link>
            </div>
            <div className="mt-4 grid gap-3">
              {missingBars.length ? missingBars.map((item) => (
                <div key={item.name}>
                  <div className="flex justify-between text-sm"><span className="font-medium text-slate-700">{item.name}</span><span>{item.pct.toFixed(1)}%</span></div>
                  <progress className={`mt-1 h-2 w-full overflow-hidden rounded-full ${missingAccent[item.severity] || 'accent-orange-500'}`} max={100} value={Math.min(100, item.pct)} />
                </div>
              )) : <p className="rounded-md bg-green-50 p-3 text-sm text-green-800">No missing values were detected.</p>}
            </div>
          </div>

          <div className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="font-semibold text-slate-950">Top cleanup priorities</h2>
                <p className="mt-1 text-sm text-slate-500">Start here before sharing the dataset downstream.</p>
              </div>
              <Link className="text-sm font-semibold text-teal-700" to={`/audit/${result.audit_id}/issues`}>Filter findings</Link>
            </div>
            <div className="mt-4 grid gap-3">
              {topIssues.length ? topIssues.map((rule) => (
                <article key={`${rule.rule_id}-${rule.description}`} className="rounded-md border border-stone-200 bg-stone-50 p-4">
                  <div className="flex items-center justify-between gap-3"><h3 className="font-semibold text-slate-900">{rule.rule_name}</h3><SeverityBadge severity={rule.severity} /></div>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{rule.suggested_fix}</p>
                </article>
              )) : <p className="text-sm text-slate-500">No rule findings were detected.</p>}
            </div>
          </div>
        </section>

        <section className="mt-6 rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h2 className="font-semibold text-slate-950">Column risk ranking</h2>
              <p className="mt-1 text-sm text-slate-500">Sort the table to decide where to drill in first.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              {[
                ['risk', 'Risk'],
                ['issues', 'Issues'],
                ['completeness', 'Completeness'],
                ['name', 'Name'],
              ].map(([key, label]) => (
                <button key={key} className={`rounded-full px-3 py-1.5 text-sm font-semibold ${sortKey === key ? 'bg-teal-700 text-white' : 'bg-stone-100 text-slate-700 hover:bg-stone-200'}`} onClick={() => setSortKey(key as typeof sortKey)}>
                  {label}
                </button>
              ))}
            </div>
          </div>
          <div className="mt-5 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b text-slate-500"><tr><th className="py-2">Column</th><th>Type</th><th>Completeness</th><th>Issues</th><th>Worst severity</th></tr></thead>
              <tbody>
                {rankedColumns.map(({ name, stats, rules, completeness }) => {
                  return (
                    <tr key={name} className="cursor-pointer border-b last:border-0 hover:bg-stone-50" onClick={() => navigate(`/audit/${result.audit_id}/column/${encodeURIComponent(name)}`)}>
                      <td className="py-3 font-semibold text-slate-900"><span className="text-teal-800 hover:underline">{name}</span></td>
                      <td>{stats.inferred_type}</td>
                      <td>{completeness.toFixed(1)}%</td>
                      <td>{rules.length}</td>
                      <td><SeverityBadge severity={worstSeverity(rules)} /></td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </section>

        <section className="mt-6 rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
          <h2 className="font-semibold text-slate-950">Completeness heatmap</h2>
          <p className="mt-1 text-sm text-slate-500">A quick scan of how complete each column is.</p>
          <div className="mt-4 grid gap-3">
            {profileEntries.map(([name, stats]: any) => {
              const completeness = 100 - Number(stats.null_pct || 0)
              return (
                <Link key={name} className="grid gap-2 rounded-md p-1 hover:bg-stone-50 md:grid-cols-[180px_1fr_70px] md:items-center" to={`/audit/${result.audit_id}/column/${encodeURIComponent(name)}`}>
                  <span className="text-sm font-medium text-slate-700">{name}</span>
                  <progress className={`h-3 w-full overflow-hidden rounded-full ${completenessColor(completeness)}`} max={100} value={completeness} />
                  <span className="text-sm text-slate-600">{completeness.toFixed(1)}%</span>
                </Link>
              )
            })}
          </div>
        </section>

        <ScoreBreakdownPanel items={scoreBreakdown(result)} totalDeduction={result.scoring?.calculation_detail?.weighted_penalty_sum} overallScore={score} />
      </div>
      {agentOpen ? <AiAgentPage panelMode onClose={() => setAgentOpen(false)} /> : null}
    </main>
  )
}
