import React, { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useAuditResult } from '../hooks/useAuditResult'
import { useAuditStore } from '../store/auditStore'
import { AuditResult, ChatMessage } from '../types/audit'
import { scoreTier } from '../utils/audit'

type Props = { panelMode?: boolean; onClose?: () => void }
type AgentProvider = 'groq' | 'groq_rate_limited' | 'local' | null

function generateChips(auditResult: AuditResult): string[] {
  const chips: string[] = []
  const score = auditResult.scoring?.overall_score ?? 0
  const findings = auditResult.rule_results ?? []
  const severityOrder: Record<string, number> = { Critical: 0, High: 1, Medium: 2, Low: 3 }

  const sorted = [...findings].sort(
    (a, b) => (severityOrder[a.severity] ?? 3) - (severityOrder[b.severity] ?? 3),
  )

  chips.push(`Why is my score ${score}/100?`)

  const critical = sorted.filter((finding) => finding.severity === 'Critical').slice(0, 2)
  for (const finding of critical) {
    const col = finding.affected_columns?.[0] ?? 'this column'
    chips.push(`What does the ${finding.rule_name} on '${col}' mean?`)
  }

  if (sorted.length > 0) {
    const col = sorted[0].affected_columns?.[0] ?? 'the main issue'
    chips.push(`How do I fix '${col}'?`)
  }

  chips.push('Which issue should I fix first?')
  chips.push('How does this affect my dashboards?')

  return [...new Set(chips)].slice(0, 6)
}

function providerText(provider: AgentProvider) {
  if (provider === 'groq') return 'Powered by Groq · Llama 3.3 70B  |  No raw data sent to AI'
  if (provider === 'groq_rate_limited') return 'Groq rate limit reached — using rule-based responses  |  Try again in 30s'
  if (provider === null) return 'Ask a question to connect the agent  |  No raw data is sent to AI'
  return 'Using rule-based responses  |  Add GROQ_API_KEY for AI answers'
}

function providerClasses(provider: AgentProvider) {
  if (provider === 'groq') return 'border-emerald-200 bg-emerald-50 text-emerald-800'
  if (provider === 'groq_rate_limited') return 'border-amber-200 bg-amber-50 text-amber-800'
  if (provider === 'local') return 'border-slate-200 bg-slate-50 text-slate-700'
  return 'border-teal-200 bg-teal-50 text-teal-800'
}

export default function AiAgentPage({ panelMode = false, onClose }: Props) {
  const { auditId, result, loading, error } = useAuditResult()
  const loadChatHistory = useAuditStore((s) => s.loadChatHistory)
  const appendChatMessage = useAuditStore((s) => s.appendChatMessage)
  const clearChatHistory = useAuditStore((s) => s.clearChatHistory)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [question, setQuestion] = useState('')
  const [sending, setSending] = useState(false)
  const [sendError, setSendError] = useState(false)
  const [provider, setProvider] = useState<AgentProvider>(null)

  useEffect(() => {
    if (auditId) setMessages(loadChatHistory(auditId))
  }, [auditId, loadChatHistory])

  const tier = scoreTier(result?.scoring?.overall_score)
  const chips = useMemo(() => result ? generateChips(result) : [], [result])

  const opening = useMemo(() => {
    if (!result) return ''
    const score = result.scoring?.overall_score ?? 0
    const issues = result.rule_results || []
    const criticalCount = issues.filter((finding) => finding.severity === 'Critical').length
    if (tier.label === 'Good') {
      return `I've reviewed the audit for ${result.dataset.filename}. The dataset scored ${score}/100 — a Good result, which means it is usable with minor cleanup. What would you like to understand better?`
    }
    if (tier.label === 'High Risk') {
      return `I've reviewed the audit for ${result.dataset.filename}. The dataset scored ${score}/100 — High Risk. There are ${issues.length} issues detected, including ${criticalCount} Critical. I'd recommend addressing those before using this data for reporting or analysis. Where would you like to start?`
    }
    return `I've reviewed the audit for ${result.dataset.filename}. The dataset scored ${score}/100 — ${tier.label}. Ask me about the findings, affected columns, or cleanup priorities.`
  }, [result, tier.label])

  const sendQuestion = async (text = question) => {
    if (!auditId || !result || !text.trim()) return
    setSending(true)
    setSendError(false)
    const userMessage: ChatMessage = { role: 'user', text: text.trim(), timestamp: new Date().toISOString() }
    setMessages((prev) => [...prev, userMessage])
    appendChatMessage(auditId, userMessage)
    try {
      const response = await api.agentMessage(text.trim(), result, messages)
      setProvider((response.provider || response.source || 'local') as AgentProvider)
      const assistantMessage: ChatMessage = { role: 'assistant', text: response.reply || response.answer, timestamp: new Date().toISOString() }
      setMessages((prev) => [...prev, assistantMessage])
      appendChatMessage(auditId, assistantMessage)
      setQuestion('')
    } catch {
      setSendError(true)
    } finally {
      setSending(false)
    }
  }

  const clearChat = () => {
    if (!auditId) return
    clearChatHistory(auditId)
    setMessages([])
    setProvider(null)
    setSendError(false)
  }

  const body = (
    <div className={panelMode ? 'fixed inset-y-0 right-0 z-50 flex w-full max-w-xl flex-col border-l border-stone-200 bg-white shadow-2xl' : 'mx-auto min-h-screen max-w-5xl bg-stone-50 px-6 py-6'}>
      <header className="border-b border-stone-200 bg-white p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-slate-950">AI Audit Agent</h1>
            {result ? <p className="mt-1 text-sm text-slate-600">{result.dataset.filename} • {result.scoring?.overall_score}/100 • {tier.label}</p> : null}
          </div>
          <div className="flex items-center gap-2">
            {messages.length ? <button className="rounded-md border border-stone-300 px-3 py-1.5 text-sm font-semibold hover:bg-stone-50" onClick={clearChat}>Clear chat</button> : null}
            {panelMode ? <button className="rounded-md border border-stone-300 px-3 py-1.5 text-sm font-semibold hover:bg-stone-50" onClick={onClose}>Close</button> : auditId ? <Link className="text-sm font-semibold text-teal-700" to={`/audit/${auditId}`}>Dashboard</Link> : null}
          </div>
        </div>
      </header>

      <section className="flex-1 overflow-y-auto p-5">
        {loading ? <div className="h-24 animate-pulse rounded-lg bg-slate-200" /> : null}
        {error ? <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        {result ? (
          <>
            <div className="rounded-lg border border-teal-200 bg-teal-50 p-4 text-sm leading-6 text-teal-950">{opening}</div>
            <div className="mt-4 flex flex-wrap gap-2">
              {chips.map((chip) => <button key={chip} className="rounded-full border border-stone-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:border-teal-300 hover:bg-teal-50" onClick={() => sendQuestion(chip)}>{chip}</button>)}
            </div>
            <div className="mt-5 grid gap-3">
              {messages.length ? messages.map((message, index) => (
                <article key={`${message.role}-${index}`} className={`rounded-lg border p-3 ${message.role === 'assistant' ? 'border-teal-200 bg-teal-50' : 'border-stone-200 bg-white'}`}>
                  <div className="text-xs font-bold uppercase tracking-wide text-slate-500">{message.role === 'assistant' ? 'AI assistant' : 'You'}</div>
                  <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-800">{message.text}</p>
                </article>
              )) : <p className="text-sm text-slate-500">Conversation history will appear here.</p>}
            </div>
          </>
        ) : null}
      </section>

      <footer className="border-t border-stone-200 bg-white p-5">
        {sendError ? <p className="mb-3 rounded-md bg-red-50 p-3 text-sm text-red-700">The agent could not answer. Try again.</p> : null}
        <textarea className="h-24 w-full rounded-md border border-stone-300 p-3 text-sm outline-none focus:border-teal-500" onChange={(event) => setQuestion(event.target.value)} placeholder="Ask about columns, counts, percentages, risk, or cleanup..." value={question} />
        <button className="mt-3 rounded-md bg-teal-700 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50" disabled={sending || !question.trim()} onClick={() => sendQuestion()}>
          {sending ? 'Sending...' : 'Send question'}
        </button>
        <div className={`mt-3 rounded-md border px-3 py-2 text-xs font-medium ${providerClasses(provider)}`}>
          {providerText(provider)}
        </div>
        {messages.length && provider === null ? <p className="mt-2 text-xs text-slate-500">Older saved messages may reflect a previous backend session. Use Clear chat before testing a new provider setup.</p> : null}
      </footer>
    </div>
  )

  return panelMode ? <div className="fixed inset-0 z-40 bg-slate-950/30">{body}</div> : body
}
