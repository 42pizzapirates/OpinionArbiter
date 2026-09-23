<script setup>
import { computed, ref, onUnmounted, nextTick } from 'vue'
import { startHost, stopHost, getHostDiscussionLog } from '../composables/api.js'
import { DEFAULT_RESEARCH_DIMENSIONS } from '../constants/roles.js'
import HostDiscussionControls from '../components/HostDiscussionControls.vue'
import HostDiscussionDimensionList from '../components/HostDiscussionDimensionList.vue'
import HostDiscussionEmptyState from '../components/HostDiscussionEmptyState.vue'
import HostDiscussionFinalMessages from '../components/HostDiscussionFinalMessages.vue'

const messages = ref([])
const researchDimensions = ref(DEFAULT_RESEARCH_DIMENSIONS)
const loading = ref(false)
const hostRunning = ref(false)
const error = ref('')
let pollTimer = null

const finalHostMessages = computed(() =>
  messages.value.filter(msg => msg.source === 'host' && !msg.dimension_key)
)

const dimensionRows = computed(() =>
  researchDimensions.value.map(dimension => {
    const scoped = messages.value.filter(msg => msg.dimension_key === dimension.key)
    return {
      ...dimension,
      insight: latestBySpeaker(scoped, 'insight'),
      media: latestBySpeaker(scoped, 'media'),
      host: latestBySpeaker(scoped, 'host'),
      count: scoped.length,
    }
  })
)

const hasStructuredMessages = computed(() =>
  finalHostMessages.value.length || dimensionRows.value.some(row => row.count)
)

function latestBySpeaker(items, source) {
  return [...items].reverse().find(msg => msg.source === source) || null
}

function normalizeDiscussionRecords(data) {
  const records = data?.discussion_records || data?.parsed_messages || []
  return records.map(record => ({
    source: record.source || '',
    message_text: record.message_text || record.content || '',
    sent_at: record.sent_at || record.timestamp || '',
    dimension_key: record.dimension_key || record.section_key || '',
  }))
}

async function handleStart() {
  error.value = ''
  try {
    await startHost()
    hostRunning.value = true
    startPolling()
  } catch (e) {
    error.value = '启动主持人失败'
  }
}

async function handleStop() {
  hostRunning.value = false
  stopPolling()
  try {
    await stopHost()
  } catch (e) {
    error.value = '停止主持人失败'
  }
}

async function refreshLog() {
  loading.value = true
  try {
    const data = await getHostDiscussionLog()
    const nextMessages = normalizeDiscussionRecords(data)
    const shouldUpdate = hasDiscussionChanged(nextMessages)
    const shouldFollow = isNearBottom()
    if (shouldUpdate) {
      messages.value = nextMessages
      await nextTick()
      if (shouldFollow) scrollToBottom()
    }
    if (isDiscussionComplete()) {
      hostRunning.value = false
      stopPolling()
    }
  } catch {}
  loading.value = false
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(refreshLog, 3000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function isDiscussionComplete() {
  return finalHostMessages.value.length > 0 && dimensionRows.value.every(row => row.host)
}

function hasDiscussionChanged(nextMessages) {
  if (nextMessages.length !== messages.value.length) return true
  const currentLast = messages.value[messages.value.length - 1]
  const nextLast = nextMessages[nextMessages.length - 1]
  return JSON.stringify(currentLast) !== JSON.stringify(nextLast)
}

function isNearBottom() {
  const el = document.querySelector('.host-discussion-content')
  if (!el) return true
  return el.scrollHeight - el.scrollTop - el.clientHeight < 80
}

function scrollToBottom() {
  const el = document.querySelector('.host-discussion-content')
  if (el) el.scrollTop = el.scrollHeight
}

onUnmounted(stopPolling)

refreshLog()
</script>

<template>
  <div class="host-discussion-view">
    <header class="view-header stagger-1">
      <div class="header-overline">HOST DISCUSSION</div>
      <h2 class="view-title">主持人研判讨论</h2>
      <p class="view-desc">主持人按五个研究维度对齐双 Agent 输出，沉淀阶段裁判与最终研判</p>
    </header>

    <HostDiscussionControls
      :running="hostRunning"
      :loading="loading"
      @start="handleStart"
      @stop="handleStop"
      @refresh="refreshLog"
    />

    <div v-if="error" class="error-msg">{{ error }}</div>

    <div v-if="messages.length" class="host-discussion-content stagger-3">
      <HostDiscussionFinalMessages :messages="finalHostMessages" />
      <HostDiscussionDimensionList v-if="hasStructuredMessages" :rows="dimensionRows" />
    </div>

    <HostDiscussionEmptyState v-else :running="hostRunning" />
  </div>
</template>

<style scoped>
.view-header {
  margin-bottom: 2rem;
}

.header-overline {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  letter-spacing: 0.25em;
  color: var(--amber);
  opacity: 0.7;
  margin-bottom: 0.5rem;
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

.error-msg {
  margin-bottom: 1rem;
  padding: 0.8rem 1rem;
  color: var(--red);
  background: var(--red-ghost);
  border: 1px solid rgba(196, 75, 60, 0.25);
  border-radius: var(--radius);
  font-size: 0.82rem;
}

.host-discussion-content {
  max-height: 66vh;
  overflow-y: auto;
  padding-right: 0.5rem;
}
</style>
