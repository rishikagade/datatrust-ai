import '@testing-library/jest-dom'

// Mock ResizeObserver for charts and responsive container rendering in jsdom
if (typeof window.ResizeObserver === 'undefined') {
  class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  window.ResizeObserver = ResizeObserver as any
}
