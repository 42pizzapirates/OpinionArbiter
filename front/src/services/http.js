const BASE = '/api'

export async function request(method, path, body = null) {
  const options = {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {}
  }
  if (body) options.body = JSON.stringify(body)

  const response = await fetch(`${BASE}${path}`, options)
  if (!response.ok) {
    const detail = await response.text().catch(() => 'Unknown error')
    throw new Error(detail || `HTTP ${response.status}`)
  }

  const contentType = response.headers.get('content-type') || ''
  return contentType.includes('application/json') ? response.json() : response.text()
}
