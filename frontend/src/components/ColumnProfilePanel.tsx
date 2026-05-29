import React from 'react'

export default function ColumnProfilePanel({ profileStats }: { profileStats: Record<string, any> }) {
  const columns = Object.entries(profileStats)
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="font-semibold text-slate-950">Column profile</h2>
      <div className="mt-4 grid gap-3">
        {columns.length ? columns.map(([name, stats]) => (
          <article key={name} className="rounded-md border border-slate-200 p-4">
            <div className="flex flex-wrap justify-between gap-3">
              <h3 className="font-semibold text-slate-900">{name}</h3>
              <span className="text-sm text-slate-500">{stats.inferred_type}</span>
            </div>
            <p className="mt-2 text-sm text-slate-600">{stats.null_count} nulls • {stats.unique_count} unique values</p>
          </article>
        )) : <p className="text-sm text-slate-500">No column profile data is available.</p>}
      </div>
    </section>
  )
}
