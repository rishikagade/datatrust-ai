import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import FileDropzone from '../components/FileDropzone'
import { api } from '../api/client'
import { useAuditStore } from '../store/auditStore'

type DemoDataset = { name: string; label: string; description: string }

const fallbackDemos: DemoDataset[] = [
  { name: 'customer_master', label: 'Customer master', description: 'Customer records with duplicate keys and missing emails.' },
  { name: 'sales_transactions', label: 'Sales transactions', description: 'Sales orders with mixed dates and business rule failures.' },
  { name: 'hr_employees', label: 'HR employees', description: 'Employee records with sparse termination dates and salary outliers.' },
]

export default function UploadPage() {
  const navigate = useNavigate()
  const setResult = useAuditStore((s) => s.setAuditResult)
  const setDemoMode = useAuditStore((s) => s.setDemoMode)
  const [demos, setDemos] = useState(fallbackDemos)
  const [busyDemo, setBusyDemo] = useState<string | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    api.demoList().then((list) => Array.isArray(list) && setDemos(list)).catch(() => undefined)
  }, [])

  const onAudit = (audit: any, demo = false) => {
    setDemoMode(demo)
    setResult(audit)
    navigate(`/audit/${audit.audit_id}`)
  }

  const loadDemo = async (name: string) => {
    setBusyDemo(name)
    setError(false)
    try {
      onAudit(await api.demo(name), true)
    } catch {
      setError(true)
    } finally {
      setBusyDemo(null)
    }
  }

  return (
    <main className="min-h-screen bg-stone-50 px-6 py-6">
      <div className="mx-auto max-w-6xl">
        <div className="rounded-lg border border-stone-200 bg-white p-6 shadow-sm">
          <div>
            <Link className="text-sm font-semibold text-teal-700" to="/">DataTrust AI</Link>
            <h1 className="mt-2 text-3xl font-bold text-slate-950">Upload a dataset</h1>
            <p className="mt-2 max-w-2xl text-slate-600">Drop in a CSV or TSV. DataTrust AI will profile it, run the rules, score the audit, and open a dashboard with next steps.</p>
          </div>
          <div className="mt-5 grid gap-3 text-sm text-slate-600 md:grid-cols-3">
            <div className="rounded-md bg-stone-50 p-3"><span className="font-semibold text-slate-900">No row storage.</span> Files are processed ephemerally.</div>
            <div className="rounded-md bg-stone-50 p-3"><span className="font-semibold text-slate-900">Live rules.</span> Demo datasets run the same pipeline.</div>
            <div className="rounded-md bg-stone-50 p-3"><span className="font-semibold text-slate-900">Export ready.</span> PDF, CSV, JSON, and report pages.</div>
          </div>
        </div>

        <section className="mt-6 rounded-lg border border-stone-200 bg-white p-6 shadow-sm">
          <FileDropzone onResult={(audit) => onAudit(audit, false)} />
        </section>

        <section className="mt-8">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-slate-950">Try a demo dataset</h2>
              <p className="mt-1 text-sm text-slate-600">Good for exploring the dashboard before uploading your own file.</p>
            </div>
          </div>
          <div className="mt-4 grid gap-4 md:grid-cols-3">
            {demos.map((demo) => (
              <button key={demo.name} className="rounded-lg border border-stone-200 bg-white p-5 text-left shadow-sm hover:border-teal-300 hover:bg-teal-50" disabled={Boolean(busyDemo)} onClick={() => loadDemo(demo.name)}>
                <span className="block font-semibold text-slate-950">{demo.label}</span>
                <span className="mt-2 block text-sm leading-6 text-slate-600">{demo.description}</span>
                <span className="mt-4 block text-sm font-semibold text-teal-700">{busyDemo === demo.name ? 'Loading...' : 'Run live demo audit'}</span>
              </button>
            ))}
          </div>
          {error ? <p className="mt-4 text-sm font-medium text-red-700">Demo loading failed. Please retry.</p> : null}
        </section>
      </div>
    </main>
  )
}
