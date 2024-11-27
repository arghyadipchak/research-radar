<script lang="ts">
  import type { Index } from 'meilisearch'

  // @ts-ignore
  import Plotly from 'plotly.js-dist'
  import { onMount } from 'svelte'
  import { meili } from './meili'

  let index: Index<Record<string, any>>

  onMount(async () => {
    index = await meili.getIndex('documents')
    const search = await index.search('', { facets: ['keyword'], limit: 0 })

    const facetData = search.facetDistribution!['keyword']
    const labels = Object.keys(facetData)
    const values = Object.values(facetData)

    const data = [
      {
        type: 'pie',
        labels: labels,
        values: values,
        hoverinfo: 'label+percent',
        textinfo: 'percent',
        hole: 0.4
      }
    ]

    const layout = {
      showlegend: false,
      height: 400,
      width: 400
    }

    Plotly.newPlot('pieChart', data, layout, { displayModeBar: false })
  })
</script>

<div id="pieChart" class=""></div>
