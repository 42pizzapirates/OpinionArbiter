<script setup>
defineProps({
  connected: Boolean,
})
</script>

<template>
  <header class="app-header stagger-1">
    <div class="header-brand">
      <div class="brand-mark">
        <span class="brand-char">尚</span>
        <svg class="brand-ring" viewBox="0 0 56 56" fill="none">
          <rect x="2" y="2" width="52" height="52" rx="6" stroke="currentColor" stroke-width="1.5" stroke-dasharray="8 4" />
        </svg>
      </div>
      <div class="brand-text">
        <h1 class="brand-title">尚舆<span class="brand-dot">.</span></h1>
        <p class="brand-sub">Sentiment Intelligence</p>
      </div>
    </div>

    <div class="header-right">
      <div class="connection-pulse" :class="{ live: connected }">
        <span class="pulse-ring"></span>
        <span class="pulse-label">{{ connected ? 'LIVE' : 'OFFLINE' }}</span>
      </div>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.8rem 2.5rem 1.2rem;
  border-bottom: 1px solid var(--border);
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 1.2rem;
}

.brand-mark {
  position: relative;
  width: 56px; height: 56px;
  display: grid; place-items: center;
  color: var(--amber);
}

.brand-char {
  font-family: var(--font-display);
  font-size: 1.8rem;
  position: relative; z-index: 1;
}

.brand-ring {
  position: absolute; inset: 0;
  width: 100%; height: 100%;
  opacity: 0.5;
  animation: spin-slow 20s linear infinite;
}

@keyframes spin-slow {
  to { transform: rotate(360deg); }
}

.brand-text { display: flex; flex-direction: column; }
.brand-title { font-size: 1.6rem; color: var(--paper); letter-spacing: 0.03em; }
.brand-dot { color: var(--amber); }
.brand-sub {
  font-size: 0.68rem;
  color: var(--paper-muted);
  letter-spacing: 0.15em;
  text-transform: uppercase;
  font-weight: 300;
}

.connection-pulse {
  display: flex; align-items: center; gap: 0.6rem;
  padding: 0.4rem 1rem;
  border: 1px solid var(--border-strong);
  border-radius: 20px;
}

.pulse-ring {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--paper-muted);
  transition: background 0.3s, box-shadow 0.3s;
}
.connection-pulse.live .pulse-ring {
  background: var(--teal);
  box-shadow: 0 0 10px rgba(74, 157, 143, 0.6);
  animation: pulse-glow 2s ease-in-out infinite;
}

.pulse-label {
  font-family: var(--font-mono);
  font-size: 0.68rem;
  letter-spacing: 0.12em;
  color: var(--paper-muted);
  transition: color 0.3s;
}
.connection-pulse.live .pulse-label { color: var(--teal); }
</style>