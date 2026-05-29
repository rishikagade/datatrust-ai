export type RuleResult = {
  rule_id?: string
  rule_name: string
  category?: string
  affected_columns?: string[]
  affected_count?: number
  affected_pct?: number
  severity: string
  description: string
  suggested_fix?: string
  metadata?: Record<string, any>
}

export type ScoringComponent = {
  p_i: number
  weight: number
  renormalized_weight: number
  weighted_deduction?: number
  component_health?: number
}

export type ScoringResult = {
  overall_score: number
  component_scores: Record<string, ScoringComponent>
  component_weights?: Record<string, number>
  calculation_detail?: {
    weighted_penalty_sum?: number
    penalties?: Record<string, number>
    severity_multiplier?: Record<string, number>
  }
}

export type AiReport = {
  executive_summary: string
  risk_interpretation: string
  cleaning_recommendations: string
  dashboard_impact: string
  model?: string
  generated_at?: string
  warning?: string
}

export type AuditDataset = {
  filename: string
  row_count: number
  column_count: number
  uploaded_at?: string
}

export type AuditResult = {
  audit_id: string
  dataset: AuditDataset
  profile_stats?: Record<string, any>
  scoring?: ScoringResult
  rule_results?: RuleResult[]
  ai_report?: AiReport
  metadata?: {
    ai_requested?: boolean
    demo_dataset?: string
    [key: string]: any
  }
}

export type ChatMessage = {
  role: 'user' | 'assistant'
  text: string
  timestamp: string
}

export type ScoreBreakdownItem = {
  key: string
  label: string
  p_i: number
  weight: number
  weightedImpact: number
  health: number
}
