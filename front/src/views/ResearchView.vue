<script setup>
import { computed, ref } from 'vue'
import { startResearch, getLatestResults, stopHost, startHost } from '../composables/api.js'
import RoleProgressGrid from '../components/RoleProgressGrid.vue'
import SavedResultsSection from '../components/SavedResultsSection.vue'
import ResearchHero from '../components/ResearchHero.vue'

const props = defineProps({
  roleProgress: Object,
  roleResults: Object,
})

const emit = defineEmits(['research-started'])

const query = ref('')
const researching = ref(false)
const results = ref(null)
const loadingLatest = ref(false)
const researchStarted = ref(false)
const hasActiveResearch = computed(() =>
  Object.keys(props.roleProgress || {}).length > 0 || Object.keys(props.roleResults || {}).length > 0
)
const researchDisabled = computed(() => researchStarted.value || hasActiveResearch.value)

async function handleResearch() {
  if (!query.value.trim() || researching.value || researchDisabled.value) return
  researching.value = true
  researchStarted.value = true
  results.value = null
  emit('research-started')
  try {
    // 新查询前重置研判会话：stop 清空旧 Session（_done / pair_store），start 创建新 Session
    // 必须先于 startResearch，确保 host 已订阅 SECTION_READY 事件再放 agent 发事件
    await stopHost()
    await startHost()
    await startResearch(query.value.trim())
  } catch (e) {
    console.error('Research start failed:', e)
  } finally {
    researching.value = false
  }
}

async function loadLatest() {
  loadingLatest.value = true
  try {
    const data = await getLatestResults()
    if (data?.results) results.value = data.results
  } catch {}
  loadingLatest.value = false
}
</script>

<template>
  <div class="research-view">
    <ResearchHero
      v-model:query="query"
      :researching="researching"
      :research-disabled="researchDisabled"
      :loading-latest="loadingLatest"
      @research="handleResearch"
      @load-latest="loadLatest"
    />

    <RoleProgressGrid
      :role-progress="roleProgress"
      :role-results="roleResults"
    />

    <SavedResultsSection :results="results" />
  </div>
</template>
