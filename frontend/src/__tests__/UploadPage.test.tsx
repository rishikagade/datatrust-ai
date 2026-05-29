import React from 'react'
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import UploadPage from '../pages/UploadPage'
import { api } from '../api/client'
import { useAuditStore } from '../store/auditStore'

vi.mock('../api/client', () => ({
  api: {
    demoList: vi.fn(),
    demo: vi.fn(),
  },
}))

type MockedApi = typeof api

function LocationDisplay() {
  const location = useLocation()
  return <div data-testid="location">{location.pathname}</div>
}

describe('UploadPage', () => {
  beforeEach(() => {
    useAuditStore.setState({ auditResult: null, auditCache: {}, chatHistory: {}, isDemoMode: false })
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders fallback demo dataset buttons when demo list loading fails', async () => {
    const mockedApi = api as unknown as MockedApi
    mockedApi.demoList.mockRejectedValue(new Error('Network failure'))

    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<UploadPage />} />
        </Routes>
      </MemoryRouter>,
    )

    await waitFor(() => expect(mockedApi.demoList).toHaveBeenCalled())
    expect(screen.getByRole('button', { name: /customer master/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sales transactions/i })).toBeInTheDocument()
  })

  it('loads a demo dataset and navigates to the audit page', async () => {
    const mockedApi = api as unknown as MockedApi
    mockedApi.demoList.mockResolvedValue([
      { name: 'sales_transactions', label: 'Sales transactions', description: 'Sales dataset with mixed dates.' },
    ])
    mockedApi.demo.mockResolvedValue({
      audit_id: 'demo-sales',
      dataset: { filename: 'sales_transactions.csv', row_count: 70, column_count: 12 },
      ai_report: { executive_summary: 'Sales sample summary' },
    })

    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="*" element={<LocationDisplay />} />
        </Routes>
      </MemoryRouter>,
    )

    await waitFor(() => expect(mockedApi.demoList).toHaveBeenCalled())
    const demoButton = screen.getByRole('button', { name: /sales transactions/i })
    fireEvent.click(demoButton)

    await waitFor(() => expect(mockedApi.demo).toHaveBeenCalledWith('sales_transactions'))
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent('/audit/demo-sales'))
  })
})
