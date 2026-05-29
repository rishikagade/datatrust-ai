import { AuditResult, RuleResult, ScoreBreakdownItem } from '../types/audit'

export const severityRank: Record<string, number> = { Critical: 0, High: 1, Medium: 2, Low: 3 }

export function scoreTier(score?: number) {
  if (score === undefined || score === null) return { label: 'Unknown', interpretation: 'Run an audit to calculate a quality tier.' }
  if (score >= 90) return { label: 'Excellent', interpretation: 'The dataset is ready for most reporting workflows.' }
  if (score >= 75) return { label: 'Good', interpretation: 'The dataset is usable with a small amount of cleanup.' }
  if (score >= 60) return { label: 'Needs Review', interpretation: 'Several issues should be corrected before high-stakes use.' }
  return { label: 'High Risk', interpretation: 'Critical cleanup is recommended before analysis or modeling.' }
}

export function scoreBreakdown(result?: AuditResult | null): ScoreBreakdownItem[] {
  if (!result?.scoring?.component_scores) return []
  return Object.entries(result.scoring.component_scores).map(([key, comp]: any) => {
    const p_i = Number(comp.p_i || 0)
    const weight = Number(comp.weight || 0)
    const weightedImpact = Number(comp.weighted_deduction ?? (weight * p_i) / 100)
    return {
      key,
      label: key.replace(/_/g, ' ').replace(/\b\w/g, (m) => m.toUpperCase()),
      p_i,
      weight,
      weightedImpact,
      health: Number(comp.component_health ?? Math.max(0, 100 - p_i)),
    }
  })
}

export function rulesByCategory(rules: RuleResult[] = []) {
  return rules.reduce<Record<string, RuleResult[]>>((groups, rule) => {
    const key = rule.category || 'Other'
    groups[key] = groups[key] || []
    groups[key].push(rule)
    return groups
  }, {})
}

export function sortedRules(rules: RuleResult[] = []) {
  return [...rules].sort((a, b) => (severityRank[a.severity] ?? 9) - (severityRank[b.severity] ?? 9))
}

export function columnIssueMap(result?: AuditResult | null) {
  const map: Record<string, RuleResult[]> = {}
  result?.rule_results?.forEach((rule) => {
    ;(rule.affected_columns || []).forEach((column) => {
      map[column] = map[column] || []
      map[column].push(rule)
    })
  })
  return map
}

export function worstSeverity(rules: RuleResult[] = []) {
  return sortedRules(rules)[0]?.severity || 'Low'
}

export function completenessColor(pct: number) {
  if (pct >= 95) return 'bg-green-500'
  if (pct >= 80) return 'bg-amber-400'
  if (pct >= 60) return 'bg-orange-500'
  return 'bg-red-500'
}

export function makeMarkdownReport(result: AuditResult) {
  const report = result.ai_report
  return [
    `# DataTrust AI Report: ${result.dataset.filename}`,
    '',
    `Score: ${result.scoring?.overall_score ?? 'N/A'}/100`,
    '',
    `## Executive Summary\n${report?.executive_summary ?? ''}`,
    `## Risk Interpretation\n${report?.risk_interpretation ?? ''}`,
    `## Cleaning Recommendations\n${report?.cleaning_recommendations ?? ''}`,
    `## Dashboard And Model Impact\n${report?.dashboard_impact ?? ''}`,
  ].join('\n\n')
}
