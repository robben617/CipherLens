const STORAGE_KEY = 'cipherlens.client_id'
const CLIENT_ID_RE = /^c_[0-9a-f]{32}$/

function randomHex(): string {
  const bytes = new Uint8Array(16)
  if (typeof crypto !== 'undefined' && typeof crypto.getRandomValues === 'function') {
    crypto.getRandomValues(bytes)
  } else {
    for (let index = 0; index < bytes.length; index++) {
      bytes[index] = Math.floor(Math.random() * 256)
    }
  }
  return Array.from(bytes, (value) => value.toString(16).padStart(2, '0')).join('')
}

export function getClientId(): string {
  try {
    const existing = localStorage.getItem(STORAGE_KEY)
    if (existing && CLIENT_ID_RE.test(existing)) return existing
  } catch {
    // 隐私模式禁用 localStorage 时退化为每次生成，不阻塞提交。
  }

  const id = `c_${randomHex()}`
  try {
    localStorage.setItem(STORAGE_KEY, id)
  } catch {
    // 同上：无法持久化时仍返回本次可用 ID。
  }
  return id
}