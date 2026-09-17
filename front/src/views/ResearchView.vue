<script setup>
import { ref } from 'vue'
import { startResearch, getLatestResults } from '../composables/api.js'
import RoleProgressGrid from '../components/RoleProgressGrid.vue'
import SavedResultsSection from '../components/SavedResultsSection.vue'
import ResearchHero from '../components/ResearchHero.vue'

defineProps({
  roleProgress: Object,
  roleResults: Object,
})

const emit = defineEmits(['research-started'])

const query = ref('')
const researching = ref(false)
const results = ref(null)
const loadingLatest = ref(false)

async function handleResearch() {
  if (!query.value.trim() || researching.value) return
  researching.value = true
  results.value = null
  emit('research-started')
  try {
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
