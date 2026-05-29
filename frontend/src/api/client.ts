const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000'

export const api = {
  audit: async (file: File) => {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${BACKEND_URL}/audit`, { method: 'POST', body: form })
    if (!res.ok) {
      const txt = await res.text()
      throw new Error(txt || res.statusText)
    }
    return res.json()
  },
  getAuditById: async (auditId: string) => {
    const res = await fetch(`${BACKEND_URL}/audit/${encodeURIComponent(auditId)}`)
    if (!res.ok) {
      const txt = await res.text()
      throw new Error(txt || res.statusText)
    }
    return res.json()
  },
  demoList: async () => {
    const res = await fetch(`${BACKEND_URL}/demo`)
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  },
  demo: async (name: string) => {
    const res = await fetch(`${BACKEND_URL}/demo/${encodeURIComponent(name)}`)
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  },
  auditChat: async (auditId: string, question: string) => {
    const res = await fetch(`${BACKEND_URL}/audit/${encodeURIComponent(auditId)}/assistant`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    })
    if (!res.ok) {
      const text = await res.text()
      throw new Error(text || res.statusText)
    }
    return res.json()
  },
  agentMessage: async (message: string, auditContext: any, conversationHistory: any[] = []) => {
    const res = await fetch(`${BACKEND_URL}/agent/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, audit_context: auditContext, conversation_history: conversationHistory }),
    })
    if (!res.ok) throw new Error('Unable to reach the audit agent.')
    return res.json()
  },
  pdfReport: async (audit: any) => {
    const res = await fetch(`${BACKEND_URL}/report/pdf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(audit),
    })
    if (!res.ok) throw new Error('Unable to generate the PDF report.')
    return res.blob()
  }
}
