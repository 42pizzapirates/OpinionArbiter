export const ROLE_LABELS = {
  insight: '数据挖掘',
  media: '舆情分析',
}

export const ROLE_SUBTITLE = {
  insight: '数据库深度检索',
  media: '全媒体舆情监控',
}

export const RESEARCH_ROLE_ORDER = ['insight', 'media']

export const SENDER_STYLE = {
  insight: { color: 'var(--amber)', icon: '◆', label: '数据挖掘', role: '数据挖掘' },
  media: { color: 'var(--blue-steel)', icon: '◇', label: '舆情分析', role: '舆情分析' },
  host: { color: 'var(--paper)', icon: '◈', label: '主持人', role: '主持人' },
}

export const DEFAULT_RESEARCH_DIMENSIONS = [
  { key: 'background_overview', title: '事件背景与概览', index: '01' },
  { key: 'heat_and_spread', title: '舆情热度与传播', index: '02' },
  { key: 'sentiment_and_opinion', title: '公众情感与观点', index: '03' },
  { key: 'platform_and_group_diff', title: '平台与群体差异', index: '04' },
  { key: 'deep_causes_and_impact', title: '深层原因与影响', index: '05' },
]
