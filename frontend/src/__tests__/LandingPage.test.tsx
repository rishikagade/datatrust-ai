import React from 'react'
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import LandingPage from '../pages/LandingPage'
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

describe('LandingPage', () => {
  beforeEach(() => {
    useAuditStore.setState({ auditResult: null, auditCache: {}, chatHistory: {}, isDemoMode: false })
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('loads demo dataset list and navigates to the audit route after clicking a demo button', async () => {
    const mockedApi = api as unknown as MockedApi
    mockedApi.demoList.mockResolvedValue([
      { name: 'customer_master', label: 'Customer master', description: 'Customer records with duplicate keys.' },
    ])
    mockedApi.demo.mockResolvedValue({
      audit_id: 'demo-1',
      dataset: { filename: 'customer_master.csv', row_count: 100, column_count: 8 },
      ai_report: { executive_summary: 'Demo summary' },
    })

    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="*" element={<LocationDisplay />} />
        </Routes>
      </MemoryRouter>,
    )

    await waitFor(() => expect(mockedApi.demoList).toHaveBeenCalled())
    const button = screen.getByRole('button', { name: /customer master/i })

    fireEvent.click(button)

    await waitFor(() => expect(mockedApi.demo).toHaveBeenCalledWith('customer_master'))
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent('/audit/demo-1'))
  })

  it('shows an error message when demo loading fails', async () => {
    const mockedApi = api as unknown as MockedApi
    mockedApi.demoList.mockResolvedValue([
      { name: 'customer_master', label: 'Customer master', description: 'Customer records with duplicate keys.' },
    ])
    mockedApi.demo.mockRejectedValue(new Error('Backend unavailable'))

    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
        </Routes>
      </MemoryRouter>,
    )

    await waitFor(() => expect(mockedApi.demoList).toHaveBeenCalled())
    const button = screen.getByRole('button', { name: /customer master/i })
    fireEvent.click(button)

    await waitFor(() => expect(screen.getByText(/demo loading failed/i)).toBeInTheDocument())
  })
})
