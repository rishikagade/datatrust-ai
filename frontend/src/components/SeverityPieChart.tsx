import React from 'react'
import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'

type DataItem = { name: string; value: number }

const severityPalette: Record<string, string> = {
  Critical: '#dc2626',
  High: '#ea580c',
  Medium: '#d97706',
  Low: '#16a34a',
}

export default function SeverityPieChart({ data }: { data: DataItem[] }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="font-semibold text-slate-950">Severity distribution</h2>
      {data.length ? (
        <div className="mt-4 h-72 w-full">
          <ResponsiveContainer>
            <PieChart>
              <Pie data={data} dataKey="value" nameKey="name" innerRadius={70} outerRadius={110} label>
                {data.map((entry) => <Cell key={entry.name} fill={severityPalette[entry.name] || '#64748b'} />)}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="mt-4 text-sm text-slate-500">No issue severity data is available.</p>
      )}
    </div>
  )
}
