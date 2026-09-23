<script setup>
import { ref } from 'vue'
import { getReportStatus, generateReport, getReportResult, getMarkdownUrl, getReportDownloadUrl } from '../composables/api.js'

const status = ref(null)
const generating = ref(false)
const reportQuery = ref('智能舆情分析报告')
const taskId = ref('')
const reportHtml = ref('')
const error = ref('')
const pollCount = ref(0)

async function refreshStatus() {
  try {
    status.value = await getReportStatus()
  } catch {}
}

async function startReport() {
  if (!status.value?.prepared) {
    error.value = '输入文件未准备就绪'
    return
  }
  generating.value = true
  error.value = ''
  reportHtml.value = ''
  pollCount.value = 0
  try {
    const res = await generateReport(reportQuery.value)
    if (res?.task_id) {
      taskId.value = res.task_id
      pollResult(res.task_id)
    }
  } catch (e) {
    error.value = e.message || '报告生成失败'
    generating.value = false
  }
}

async function pollResult(tid) {
  const maxPolls = 90
  for (let i = 0; i < maxPolls; i++) {
    await new Promise(r => setTimeout(r, 2000))
    try {
      const html = await getReportResult(tid)
      pollCount.value = i + 1
      if (html && !html.includes('尚未完成')) {
        reportHtml.value = html
        generating.value = false
        return
      }
    } catch {}
  }
  error.value = '报告生成超时，请稍后重试'
  generating.value = false
}

function downloadReport() {
  window.open(getReportDownloadUrl(taskId.value), '_blank')
}

function downloadMarkdown() {
  window.open(getMarkdownUrl(taskId.value), '_blank')
}

refreshStatus()
</script>

<template>
  <div class="report-view">
    <header class="view-header stagger-1">
      <div class="header-overline">REPORT</div>
      <h2 class="view-title">综合报告生成</h2>
      <p class="view-desc">基于主持人裁判与双 Agent 证据，LLM 自动生成完整的舆情研究报告</p>
    </header>

    <!-- Status bar -->
    <div class="status-bar stagger-2">
      <div class="status-grid">
        <div class="status-cell" v-if="status">
          <span class="status-key">输入就绪</span>
          <span class="status-val" :class="{ ok: status.prepared }">
            <span class="status-dot" :class="{ ok: status.prepared }"></span>
            {{ status.prepared ? '已就绪' : '未就绪' }}
          </span>
        </div>
        <div class="status-cell" v-if="status?.found_files?.length">
          <span class="status-key">可用文件</span>
          <span class="status-val">{{ status.found_files.length }} 个</span>
        </div>
        <div class="status-cell" v-if="generating">
          <span class="status-key">轮询次数</span>
          <span class="status-val">{{ pollCount }}</span>
        </div>
      </div>
      <button class="refresh-btn" @click="refreshStatus">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M1 4v6h6M23 20v-6h-6"/>
          <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>
        </svg>
        刷新
      </button>
    </div>

    <!-- Generate -->
    <section class="generate-section stagger-3">
      <div class="generate-card">
        <div class="generate-input-wrap">
          <input
            v-model="reportQuery"
            class="generate-input"
            placeholder="输入报告主题，留空则自动聚合当前分析结果..."
            :disabled="generating"
          />
          <button class="generate-btn" @click="startReport" :disabled="generating || !reportQuery.trim() || !status?.prepared">
            <svg v-if="!generating" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="12" y1="18" x2="12" y2="12"/>
              <line x1="9" y1="15" x2="15" y2="15"/>
            </svg>
            <span v-if="!generating">生成报告</span>
            <span v-else class="generating-label">
              <span class="gen-dot"></span>
              正在生成报告...
            </span>
          </button>
        </div>
        <p class="generate-hint">LLM 将优先聚合主持人最终裁判，并结合 Insight / Media 证据生成 Markdown 与 HTML 报告</p>
      </div>
    </section>

    <!-- Error -->
    <div v-if="error" class="error-msg stagger-3">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="15" y1="9" x2="9" y2="15"/>
        <line x1="9" y1="9" x2="15" y2="15"/>
      </svg>
      {{ error }}
    </div>

    <!-- Report output -->
    <section v-if="reportHtml" class="report-output stagger-4">
      <div class="output-toolbar">
        <h3 class="output-title">报告预览</h3>
        <div class="output-actions">
          <button class="action-btn" @click="downloadReport">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            下载 HTML
          </button>
          <button class="action-btn" @click="downloadMarkdown">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            导出 Markdown
          </button>
        </div>
      </div>
      <div class="report-frame" v-html="reportHtml"></div>
    </section>
  </div>
</template>

<style scoped>
/* ================================================================
   ReportView — Editorial report generation
   ================================================================ */

.view-header {
  margin-bottom: 2rem;
}

.header-overline {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  letter-spacing: 0.25em;
  color: var(--amber);
  margin-bottom: 0.5rem;
  opacity: 0.7;
}

.view-title {
  font-size: clamp(1.8rem, 4vw, 2.4rem);
  color: var(--paper);
  margin-bottom: 0.4rem;
  letter-spacing: 0.02em;
}

.view-desc {
  color: var(--paper-dim);
  font-size: 0.9rem;
  line-height: 1.6;
}

/* Status bar */
.status-bar {
  display: flex;
  align-items: flex-start;
  gap: 1.5rem;
  padding: 1.2rem 1.5rem;
  background: var(--ink-light);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  margin-bottom: 1.8rem;
  flex-wrap: wrap;
}

.status-grid {
  display: flex;
  gap: 2.5rem;
  flex-wrap: wrap;
  flex: 1;
}

.status-cell {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.status-key {
  font-size: 0.68rem;
  color: var(--paper-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.status-val {
  font-family: var(--font-mono);
  font-size: 0.85rem;
  color: var(--paper-dim);
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.status-val.ok {
  color: var(--teal);
}

.status-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--paper-muted);
}
.status-dot.ok {
  background: var(--teal);
}

.refresh-btn {
  padding: 0.45rem 1rem;
  background: none;
  color: var(--paper-dim);
  font-size: 0.78rem;
  border: 1px solid var(--border-strong);
  border-radius: 20px;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  white-space: nowrap;
}
.refresh-btn:hover {
  border-color: var(--amber);
  color: var(--amber);
}

/* Generate section */
.generate-card {
  background: var(--ink-light);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
}

.generate-input-wrap {
  display: flex;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--ink);
  transition: border-color 0.25s, box-shadow 0.25s;
}
.generate-input-wrap:focus-within {
  border-color: var(--teal);
  box-shadow: 0 0 0 3px var(--teal-ghost);
}

.generate-input {
  flex: 1;
  border: none;
  padding: 0.9rem 1.2rem;
  font-size: 0.95rem;
  background: transparent;
  color: var(--paper);
}
.generate-input::placeholder {
  color: var(--paper-muted);
  opacity: 0.5;
}

.generate-btn {
  padding: 0.9rem 1.8rem;
  background: var(--teal);
  color: white;
  font-weight: 600;
  font-size: 0.88rem;
  letter-spacing: 0.03em;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  white-space: nowrap;
}
.generate-btn:hover:not(:disabled) {
  filter: brightness(1.15);
}

.generating-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.gen-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: white;
  animation: pulse-glow 1.2s ease-in-out infinite;
}

.generate-hint {
  margin-top: 0.8rem;
  font-size: 0.72rem;
  color: var(--paper-muted);
  letter-spacing: 0.03em;
}

/* Error */
.error-msg {
  margin-top: 1.2rem;
  padding: 1rem 1.2rem;
  color: var(--red);
  background: var(--red-ghost);
  border: 1px solid rgba(196, 75, 60, 0.25);
  border-radius: var(--radius);
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Report output */
.report-output {
  margin-top: 2.5rem;
}

.output-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.output-title {
  font-size: 1.15rem;
  color: var(--paper);
  font-family: var(--font-display);
  font-weight: 400;
}

.output-actions {
  display: flex;
  gap: 0.6rem;
}

.action-btn {
  padding: 0.5rem 1.2rem;
  background: var(--ink-light);
  color: var(--amber);
  font-size: 0.8rem;
  border: 1px solid var(--amber-ghost);
  border-radius: 20px;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  transition: border-color 0.2s, background 0.2s;
}
.action-btn:hover {
  border-color: var(--amber);
  background: var(--amber-ghost);
}

.report-frame {
  background: var(--ink-light);
  color: var(--paper);
  padding: 2.5rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  max-height: 75vh;
  overflow-y: auto;
  font-size: 0.9rem;
  line-height: 1.85;
}
.report-frame :deep(h1),
.report-frame :deep(h2),
.report-frame :deep(h3) {
  font-family: var(--font-display);
  color: var(--amber);
  margin: 1.5em 0 0.5em;
}
.report-frame :deep(h1) { font-size: 1.8rem; }
.report-frame :deep(h2) { font-size: 1.4rem; }
.report-frame :deep(h3) { font-size: 1.1rem; }
.report-frame :deep(p) { margin-bottom: 0.8em; }
.report-frame :deep(strong) { color: var(--paper); }
.report-frame :deep(a) { color: var(--amber); }
.report-frame :deep(blockquote) {
  border-left: 2px solid var(--amber);
  padding-left: 1rem;
  margin-left: 0;
  color: var(--paper-dim);
}
.report-frame :deep(code) {
  background: var(--ink);
  padding: 0.2em 0.5em;
  border-radius: 3px;
  font-size: 0.85em;
}
.report-frame :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
}
.report-frame :deep(th),
.report-frame :deep(td) {
  padding: 0.6em 1em;
  border: 1px solid var(--border);
  text-align: left;
}
.report-frame :deep(th) {
  background: var(--ink);
  color: var(--amber);
  font-weight: 500;
}
</style>
