import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuditStore } from '../store/auditStore'

type DemoDataset = { name: string; label: string; description: string }

const fallbackDemos: DemoDataset[] = [
  { name: 'customer_master', label: 'Customer master', description: 'Duplicate keys, missing emails, category variants.' },
  { name: 'sales_transactions', label: 'Sales transactions', description: 'Mixed dates, negative totals, shipping inversions.' },
  { name: 'hr_employees', label: 'HR employees', description: 'Sparse termination dates, salary outliers, ID conflicts.' },
]

export default function LandingPage() {
  const navigate = useNavigate()
  const setResult = useAuditStore((s) => s.setAuditResult)
  const setDemoMode = useAuditStore((s) => s.setDemoMode)
  const [demos, setDemos] = useState(fallbackDemos)
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    api.demoList().then((list) => Array.isArray(list) && setDemos(list)).catch(() => undefined)
  }, [])

  const loadDemo = async (name = 'customer_master') => {
    setBusy(name)
    setError(false)
    try {
      const audit = await api.demo(name)
      setDemoMode(true)
      setResult(audit)
      navigate(`/audit/${audit.audit_id}`)
    } catch {
      setError(true)
    } finally {
      setBusy(null)
    }
  }

  return (
    <main className="min-h-screen bg-stone-50">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <div className="text-lg font-bold text-slate-950">DataTrust AI</div>
        <Link className="rounded-md bg-teal-700 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-teal-800" to="/upload">Upload</Link>
      </header>

      <section className="mx-auto grid max-w-6xl gap-8 px-6 pb-14 pt-8 lg:grid-cols-[1.08fr_0.92fr] lg:items-center">
        <div>
          <p className="inline-flex rounded-full bg-teal-50 px-3 py-1 text-sm font-semibold text-teal-800">Privacy-safe data quality audits</p>
          <h1 className="mt-5 max-w-3xl text-5xl font-bold tracking-normal text-slate-950">DataTrust AI</h1>
          <p className="mt-5 max-w-2xl text-2xl font-semibold text-slate-700">Rules detect the issues. AI explains the business impact.</p>
          <p className="mt-5 max-w-2xl text-base leading-7 text-slate-600">
            Upload a CSV and get a guided audit: what is wrong, why it matters, what to fix first, and what you can safely share with stakeholders.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link className="rounded-md bg-teal-700 px-5 py-3 text-sm font-semibold text-white shadow-sm hover:bg-teal-800" to="/upload">Upload a dataset</Link>
            <button className="rounded-md border border-stone-300 bg-white px-5 py-3 text-sm font-semibold text-slate-900 hover:bg-stone-100" disabled={Boolean(busy)} onClick={() => loadDemo()}>
              {busy ? 'Loading demo...' : 'Try a demo'}
            </button>
          </div>
          {error ? <p className="mt-4 text-sm font-medium text-red-700">Demo loading failed. Please try again.</p> : null}
        </div>
        <div className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
          <div className="rounded-md bg-stone-50 p-4">
            <h2 className="font-semibold text-slate-950">Start with a realistic demo</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">Each demo runs the live backend pipeline and opens the full dashboard.</p>
          </div>
          <div className="mt-4 grid gap-3">
            {demos.map((demo) => (
              <button key={demo.name} className="rounded-md border border-stone-200 p-4 text-left hover:border-teal-300 hover:bg-teal-50" disabled={Boolean(busy)} onClick={() => loadDemo(demo.name)}>
                <span className="block font-semibold text-slate-950">{demo.label}</span>
                <span className="mt-1 block text-sm text-slate-600">{demo.description}</span>
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="border-y border-stone-200 bg-white">
        <div className="mx-auto grid max-w-6xl gap-4 px-6 py-10 md:grid-cols-3">
          {['Upload a CSV', 'Run the audit', 'Read the report'].map((title, index) => (
            <div key={title} className="rounded-lg border border-stone-200 p-5">
              <div className="text-sm font-bold text-teal-700">0{index + 1}</div>
              <h3 className="mt-2 font-semibold text-slate-950">{title}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                {index === 0 && 'Drag, drop, and the audit begins automatically.'}
                {index === 1 && '11 validation rules cover completeness, validity, uniqueness, consistency, timeliness, and integrity.'}
                {index === 2 && 'AI-written, business-ready findings are ready for dashboards, decisions, and PDF export.'}
              </p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl gap-4 px-6 py-10 md:grid-cols-3">
        {[
          ['Automated Quality Scoring', 'Weighted 0-100 score. Every point deducted is explained.'],
          ['AI-Powered Business Narratives', 'Plain-English findings for analysts and executives. No raw data leaves the audit pipeline.'],
          ['Interactive Audit Agent', 'Ask questions about your results in plain English. The agent answers from actual findings.'],
        ].map(([title, text]) => (
          <article key={title} className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
            <h3 className="font-semibold text-slate-950">{title}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">{text}</p>
          </article>
        ))}
      </section>

      <section className="bg-teal-950 px-6 py-10 text-white">
        <div className="mx-auto max-w-6xl">
          <h2 className="text-xl font-semibold">Privacy-safe by design</h2>
          <p className="mt-3 max-w-4xl leading-7 text-slate-200">
            Your data is processed ephemerally. No CSV rows are stored after the audit completes. The AI model receives only aggregated statistics — column names, counts, and percentages — never raw values from your dataset.
          </p>
        </div>
      </section>

      <footer className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6 text-sm text-slate-500">
        <span>Built as a full-stack data quality audit project.</span>
        <a className="font-semibold text-slate-700" href="https://github.com/" rel="noreferrer" target="_blank">GitHub</a>
      </footer>
    </main>
  )
}
