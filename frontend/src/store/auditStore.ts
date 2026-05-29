import { create } from 'zustand'
import { ChatMessage } from '../types/audit'

const STORAGE_KEY = 'datatrust-audit-cache'

type StoredCache = {
  auditCache: Record<string, any>
  chatHistory: Record<string, ChatMessage[]>
}

const loadStoredCache = (): StoredCache => {
  if (typeof window === 'undefined') return { auditCache: {}, chatHistory: {} }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return { auditCache: {}, chatHistory: {} }
    const parsed = JSON.parse(raw)
    return {
      auditCache: parsed.auditCache ?? {},
      chatHistory: parsed.chatHistory ?? {},
    }
  } catch {
    return { auditCache: {}, chatHistory: {} }
  }
}

const saveStoredCache = (cache: StoredCache) => {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(cache))
  } catch {
    // ignore storage failures
  }
}

type AuditStore = {
  auditResult: any | null
  auditCache: Record<string, any>
  chatHistory: Record<string, ChatMessage[]>
  setAuditResult: (r: any) => void
  loadAuditById: (auditId: string) => any | null
  loadChatHistory: (auditId: string) => ChatMessage[]
  appendChatMessage: (auditId: string, message: ChatMessage) => void
  clearChatHistory: (auditId: string) => void
  clearAuditResult: () => void
  isDemoMode: boolean
  setDemoMode: (v: boolean) => void
}

export const useAuditStore = create<AuditStore>((set, get) => {
  const stored = loadStoredCache()
  return ({
    auditResult: null,
    auditCache: stored.auditCache,
    chatHistory: stored.chatHistory,
    setAuditResult: (r) => {
      const auditId = r?.audit_id
      if (auditId) {
        const nextCache = { ...get().auditCache, [auditId]: r }
        saveStoredCache({ auditCache: nextCache, chatHistory: get().chatHistory })
        set({ auditResult: r, auditCache: nextCache })
      } else {
        set({ auditResult: r })
      }
    },
    loadAuditById: (auditId) => {
      const cached = get().auditCache[auditId]
      if (cached) {
        set({ auditResult: cached })
        return cached
      }
      return null
    },
    loadChatHistory: (auditId) => get().chatHistory[auditId] ?? [],
    appendChatMessage: (auditId, message) => {
      const current = get().chatHistory[auditId] ?? []
      const nextHistory = { ...get().chatHistory, [auditId]: [...current, message] }
      saveStoredCache({ auditCache: get().auditCache, chatHistory: nextHistory })
      set({ chatHistory: nextHistory })
    },
    clearChatHistory: (auditId) => {
      const nextHistory = { ...get().chatHistory }
      delete nextHistory[auditId]
      saveStoredCache({ auditCache: get().auditCache, chatHistory: nextHistory })
      set({ chatHistory: nextHistory })
    },
    clearAuditResult: () => set({ auditResult: null }),
    isDemoMode: false,
    setDemoMode: (v) => set({ isDemoMode: v }),
  })
})
