import MeiliSearch from 'meilisearch'

export const meili = new MeiliSearch({
  host: import.meta.env.VITE_MEILI_URL || 'http://localhost:7700',
  apiKey: import.meta.env.VITE_MEILI_API_KEY || ''
})
