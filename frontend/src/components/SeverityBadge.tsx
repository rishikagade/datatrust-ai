import React from 'react'

const classes: Record<string, string> = {
  Critical: 'bg-red-50 text-red-700 border-red-200',
  High: 'bg-orange-50 text-orange-700 border-orange-200',
  Medium: 'bg-amber-50 text-amber-700 border-amber-200',
  Low: 'bg-green-50 text-green-700 border-green-200',
}

const icons: Record<string, string> = {
  Critical: '⛔',
  High: '⚠️',
  Medium: '🔸',
  Low: 'ℹ️',
}

export default function SeverityBadge({ severity }: { severity: string }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold ${classes[severity] || 'border-slate-200 bg-slate-50 text-slate-700'}`}>
      <span>{icons[severity] || '•'}</span>
      {severity}
    </span>
  )
}
