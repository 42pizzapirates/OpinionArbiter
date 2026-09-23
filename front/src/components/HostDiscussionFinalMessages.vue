<script setup>
import { SENDER_STYLE } from '../constants/roles.js'

defineProps({
  messages: {
    type: Array,
    default: () => [],
  },
})
</script>

<template>
  <section v-if="messages.length" class="final-section">
    <div class="section-kicker">FINAL JUDGEMENT</div>
    <details
      v-for="(msg, i) in messages"
      :key="`final-${i}`"
      class="host-final"
      open
    >
      <summary>
        <div class="msg-meta">
          <span class="msg-sender" :style="{ color: SENDER_STYLE[msg.source]?.color }">
            <span class="msg-icon">{{ SENDER_STYLE[msg.source]?.icon }}</span>
            {{ SENDER_STYLE[msg.source]?.label }}
          </span>
          <span class="msg-role toggle-label"></span>
          <span class="msg-time">{{ msg.sent_at }}</span>
        </div>
      </summary>
      <div class="msg-content final-content">{{ msg.message_text }}</div>
    </details>
  </section>
</template>

<style scoped>
.final-section,
.section-kicker {
  margin-bottom: 0.7rem;
}

.section-kicker {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  letter-spacing: 0.25em;
  color: var(--amber);
  opacity: 0.7;
}

.host-final {
  padding: 1.2rem 1.4rem;
  border-left: 2px solid var(--amber);
  background: var(--ink-lighter);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
}

.host-final summary {
  cursor: pointer;
  list-style: none;
}

.host-final summary::-webkit-details-marker {
  display: none;
}

.toggle-label::after {
  content: '收起';
}

.host-final:not([open]) .toggle-label::after {
  content: '展开';
}

.final-content {
  margin-top: 0.5rem;
}

.msg-meta {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin-bottom: 0.5rem;
}

.msg-icon {
  font-size: 0.7rem;
}

.msg-sender {
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.msg-role {
  font-size: 0.65rem;
  color: var(--paper-muted);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.msg-time {
  margin-left: auto;
  font-family: var(--font-mono);
  font-size: 0.68rem;
  color: var(--paper-muted);
}

.msg-content {
  font-size: 0.84rem;
  color: var(--paper-dim);
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-word;
}

@media (max-width: 760px) {
  .msg-meta {
    flex-wrap: wrap;
  }

  .msg-time {
    margin-left: 0;
  }
}
</style>
