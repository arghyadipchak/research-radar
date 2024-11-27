import type { Config } from 'tailwindcss'

import daisyui from 'daisyui'

export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {},
  plugins: [daisyui],
  daisyui: {
    themes: ['emerald']
  }
} satisfies Config
