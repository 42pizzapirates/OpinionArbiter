import { request } from './http.js'

export function getReportStatus() {
  return request('GET', '/report/status')
}

export function generateReport(query) {
  return request('POST', '/report/generate', { query })
}

export function getReportResult(taskId) {
  return fetch(`/api/report/result/${taskId}`).then(response => response.text())
}

export function getReportDownloadUrl(taskId, fileType = 'html') {
  return `/api/report/download/${taskId}/${fileType}`
}

export function getMarkdownUrl(taskId) {
  return getReportDownloadUrl(taskId, 'md')
}