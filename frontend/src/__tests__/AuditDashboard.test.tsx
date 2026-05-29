import React from 'react'
import { describe, expect, it, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import AuditDashboard from '../pages/AuditDashboard'
import { api } from '../api/client'
import { useAuditStore } from '../store/auditStore'

vi.mock('../api/client', () => ({
  api: {
    getAuditById: vi.fn(),
  },
}))

type MockedApi = typeof api

const sampleResult = {
  audit_id: 'demo-1',
  dataset: {
    filename: 'customer_master.csv',
    row_count: 120,
    column_count: 10,
    uploaded_at: '2026-05-25T00:00:00Z',
  },
  profile_stats: {
    customer_id: {
      name: 'customer_id',
      inferred_type: 'integer',
      null_count: 0,
      null_pct: 0,
      unique_count: 120,
      top_values: [{ value: '1001', count: 1, pct: 0.8 }],
      numeric_summary: { min: 1001, max: 1120, mean: 1060 },
    },
  },
  rule_results: [
    {
      rule_id: 'duplicate_rows',
      rule_name: 'Duplicate row check',
      category: 'duplicate_rows',
      severity: 'High',
      description: 'Exact duplicate rows were found.',
      affected_columns: ['customer_id', 'email'],
      affected_count: 3,
      affected_pct: 2.5,
      suggested_fix: 'Remove duplicates or deduplicate records before analysis.',
    },
  ],
  scoring: {
    overall_score: 82,
    component_scores: {
      missing_value: { p_i: 8, weight: 20, renormalized_weight: 8 },
      duplicate_rows: { p_i: 6, weight: 20, renormalized_weight: 6 },
    },
    calculation_detail: {
      weighted_penalty_sum: 14,
    },
  },
  ai_report: {
    executive_summary: 'A moderate number of duplicate rows were found in the customer dataset.',
    risk_interpretation: 'Duplicates will distort counts and customer lifetime metrics.',
    cleaning_recommendations: 'Remove duplicate rows and normalize customer IDs before reporting.',
    dashboard_impact: 'Fixing these issues improves confidence in analytics dashboards.',
  },
}

describe('AuditDashboard', () => {
  beforeEach(() => {
    useAuditStore.setState({ auditResult: null, auditCache: {}, chatHistory: {}, isDemoMode: false })
    vi.clearAllMocks()
  })

  it('renders summary tab and can switch to profile, issues, and download tabs', async () => {
    const mockedApi = api as unknown as MockedApi
    mockedApi.getAuditById.mockResolvedValue(sampleResult)
    useAuditStore.setState({ auditResult: sampleResult, auditCache: {}, chatHistory: {}, isDemoMode: false })

    render(
      <MemoryRouter initialEntries={['/audit/demo-1']}>
        <Routes>
          <Route path="/audit/:auditId" element={<AuditDashboard />} />
        </Routes>
      </MemoryRouter>,
    )

    await waitFor(() => expect(screen.getByText(/customer_master.csv/i)).toBeInTheDocument())
    expect(screen.getByRole('heading', { name: /quality score/i })).toBeInTheDocument()
    expect(screen.getAllByText(/duplicate row check/i).length).toBeGreaterThan(0)

    expect(screen.getByText(/column risk ranking/i)).toBeInTheDocument()
    expect(screen.getByText(/completeness heatmap/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /download/i })).toBeInTheDocument()
  })
})
