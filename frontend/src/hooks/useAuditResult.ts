import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuditStore } from '../store/auditStore'
import { AuditResult } from '../types/audit'

export function useAuditResult() {
  const { auditId } = useParams<{ auditId: string }>()
  const result = useAuditStore((s) => s.auditResult) as AuditResult | null
  const setResult = useAuditStore((s) => s.setAuditResult)
  const loadAuditById = useAuditStore((s) => s.loadAuditById)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!auditId || result?.audit_id === auditId) return
    let canceled = false
    const run = async () => {
      setLoading(true)
      setError(null)
      const cached = loadAuditById(auditId)
      if (cached) {
        setLoading(false)
        return
      }
      try {
        const audit = await api.getAuditById(auditId)
        if (!canceled) setResult(audit)
      } catch {
        if (!canceled) setError('Audit not found. Load a demo or upload a dataset to continue.')
      } finally {
        if (!canceled) setLoading(false)
      }
    }
    run()
    return () => {
      canceled = true
    }
  }, [auditId, result?.audit_id, loadAuditById, setResult])

  return { auditId, result: result?.audit_id === auditId ? result : result, loading, error }
}
