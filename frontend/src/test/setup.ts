import '@testing-library/jest-dom'

// Node 21+ exposes a built-in experimental `localStorage` global that is
// undefined unless `--localstorage-file` is passed. Under the jsdom test
// environment this broken global can shadow jsdom's working implementation,
// breaking zustand's `persist` middleware (localStorage.setItem on undefined).
// Pin the global to a simple in-memory store so tests behave identically
// across Node versions (CI runs Node 22; local may run newer).
class MemoryStorage implements Storage {
  private store = new Map<string, string>()
  get length() {
    return this.store.size
  }
  clear() {
    this.store.clear()
  }
  getItem(key: string) {
    return this.store.has(key) ? this.store.get(key)! : null
  }
  key(index: number) {
    return Array.from(this.store.keys())[index] ?? null
  }
  removeItem(key: string) {
    this.store.delete(key)
  }
  setItem(key: string, value: string) {
    this.store.set(key, String(value))
  }
}

Object.defineProperty(globalThis, 'localStorage', {
  configurable: true,
  value: new MemoryStorage(),
})
