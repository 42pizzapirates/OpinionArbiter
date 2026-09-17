import { request } from './http.js'

export function startResearch(query) {
  return request('POST', '/research', { query })
}

export function getLatestResults() {
  return request('GET', '/research/latest')
}
