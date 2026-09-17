import { request } from './http.js'

export function getHostDiscussionLog() {
  return request('GET', '/host/discussion')
}
