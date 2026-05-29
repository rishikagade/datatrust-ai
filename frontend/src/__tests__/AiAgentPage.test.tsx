import React from 'react'
import { describe, expect, it, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import AiAgentPage from '../pages/AiAgentPage'
import { api } from '../api/client'
import { useAuditStore } from '../store/auditStore'

vi.mock('../api/client', () => ({
  api: {
    getAuditById: vi.fn(),
    agentMessage: vi.fn(),
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
  profile_stats: {},
  rule_results: [
    {
      rule_id: 'duplicate_rows',
      rule_name: 'Duplicate row check',
      category: 'duplicate_rows',
      severity: 'High',
      description: 'Exact duplicate rows were found.',
      affected_columns: ['customer_id', 'email'],
    },
  ],
  scoring: {
    overall_score: 82,
    component_scores: {
      duplicate_rows: { p_i: 6, weight: 20, renormalized_weight: 6 },
    },
  },
}

describe('AiAgentPage', () => {
  beforeEach(() => {
    useAuditStore.setState({ auditResult: null, auditCache: {}, chatHistory: {}, isDemoMode: false })
    vi.clearAllMocks()
  })

  it('loads audit from backend when not available in cache and shows assistant header', async () => {
    const mockedApi = api as unknown as MockedApi
    mockedApi.getAuditById.mockResolvedValue(sampleResult)

    render(
      <MemoryRouter initialEntries={['/audit/demo-1/assistant']}>
        <Routes>
          <Route path="/audit/:auditId/assistant" element={<AiAgentPage />} />
        </Routes>
      </MemoryRouter>,
    )

    await waitFor(() => expect(screen.getByText(/AI Audit Agent/i)).toBeInTheDocument())
    expect(screen.getAllByText(/customer_master\.csv/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/82\/100/i).length).toBeGreaterThan(0)
    expect(mockedApi.getAuditById).toHaveBeenCalledWith('demo-1')
  })

  it('sends a question and appends user and assistant messages', async () => {
    const mockedApi = api as unknown as MockedApi
    mockedApi.getAuditById.mockResolvedValue(sampleResult)
    mockedApi.agentMessage.mockResolvedValue({ reply: 'The audit found a few key issues.' })

    render(
      <MemoryRouter initialEntries={['/audit/demo-1/assistant']}>
        <Routes>
          <Route path="/audit/:auditId/assistant" element={<AiAgentPage />} />
        </Routes>
      </MemoryRouter>,
    )

    await waitFor(() => expect(screen.getByText(/AI Audit Agent/i)).toBeInTheDocument())

    fireEvent.change(screen.getByPlaceholderText(/Ask about columns/i), {
      target: { value: 'What should I fix first?' },
    })
    fireEvent.click(screen.getByRole('button', { name: /send question/i }))

    await waitFor(() => expect(screen.getAllByText(/What should I fix first\?/i).length).toBeGreaterThan(0))
    expect(screen.getByText(/The audit found a few key issues\./i)).toBeInTheDocument()
    expect(mockedApi.agentMessage).toHaveBeenCalled()
  })
})
