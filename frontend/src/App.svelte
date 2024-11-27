<script lang="ts">
  import { marked } from 'marked'
  import { type Index } from 'meilisearch'
  import { onMount } from 'svelte'
  import logo from './assets/logo.svg'
  import Chart from './lib/Chart.svelte'
  import { meili } from './lib/meili'
  import { getChat } from './lib/ollama'
  import { checkPaper, pdfToText } from './lib/pdf'

  const topicOptions = [
    'Machine Learning',
    'Image Processing',
    'Object Detection',
    'Computer Vision',
    'Internet Of Things',
    'Antenna',
    'Science',
    'Maths',
    'Deep Learning',
    'Statistics',
    'Natural Language Processing',
    'Large Language Models',
    'Artificial Intelligence',
    'Neural Networks',
    'Transformers',
    'Quantum Computing',
    'Cryptography',
    'Blockchain',
    'Graph Theory',
    'Cloud Computing'
  ].toSorted()
  let selectedTopics: Set<string> = new Set()
  let countTopics: number = 0

  const modelOptions = ['llama3.2', 'llama3.1', 'qwen2.5']
  let selectedModel = modelOptions[0]

  let index: Index<Record<string, any>>
  let currOffset: number = 0
  let lastOffset: number = 0
  let searchQuery = ''
  let searchResults: any[] = []
  let paperAvailable: boolean[] = []
  let expanded: boolean[] = []
  let summaryResult: string[] = []
  let loadingSummary: boolean[] = []

  onMount(async () => {
    index = await meili.getIndex('documents')
  })

  function reset() {
    searchResults = []
    paperAvailable = []
    expanded = []
    summaryResult = []
    loadingSummary = []
  }

  async function updateSearch(query: string, count: number, _: number) {
    if (!index || query === '') {
      reset()
      return
    }

    if (lastOffset == currOffset) {
      reset()
      currOffset = 0
      lastOffset = 0
    } else lastOffset = currOffset

    const response = await index.search(query, {
      offset: currOffset,
      limit: 10,
      filter: [
        count > 0 ? [...selectedTopics].map(topic => `keyword = "${topic}"`).join(' OR ') : ''
      ]
    })

    searchResults = searchResults.concat(response.hits)
    paperAvailable = paperAvailable.concat(
      await Promise.all(response.hits.map(result => checkPaper(result.paperlink)))
    )
    expanded = expanded.concat(response.hits.map(() => false))
    summaryResult = summaryResult.concat(response.hits.map(() => ''))
    loadingSummary = loadingSummary.concat(response.hits.map(() => false))
  }

  $: (async () => {
    await updateSearch(searchQuery.trim(), countTopics, currOffset)
  })()

  function checkScroll() {
    const scrollPercent =
      (window.scrollY + window.innerHeight) / document.documentElement.scrollHeight

    if (scrollPercent >= 0.9 && currOffset < 100) currOffset += 10
  }

  let scrollTimeout: number
  window.addEventListener('scroll', () => {
    if (scrollTimeout) clearTimeout(scrollTimeout)

    scrollTimeout = setTimeout(checkScroll, 100)
  })

  const toggleExpand = (index: number) => (expanded[index] = !expanded[index])

  const toggleTopic = (topic: string) => {
    selectedTopics.has(topic) ? selectedTopics.delete(topic) : selectedTopics.add(topic)
    countTopics = selectedTopics.size
  }

  const introSearch = new RegExp('introduction', 'i')
  const cache = new Map()

  async function generateHash(str: string) {
    const hashBuffer = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(str))

    return Array.from(new Uint8Array(hashBuffer))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('')
  }

  async function summarize(idx: number) {
    loadingSummary[idx] = true

    let text = await pdfToText(searchResults[idx].paperlink)
    if (text === '') {
      alert('Unable to fetch Paper!')
      loadingSummary[idx] = false

      return
    }

    const hash = await generateHash(selectedModel + '~' + text)
    if (cache.has(hash)) {
      summaryResult[idx] = cache.get(hash)
      loadingSummary[idx] = false

      return
    }

    const intro = introSearch.exec(text)
    if (intro) text = text.substring(intro.index)

    const response = await getChat(text, selectedModel)

    // text = ''
    // for await (const part of response) {
    //   text += part.message.content
    //   summaryResult[idx] = await marked.parse(text)
    // }

    summaryResult[idx] = await marked.parse(response.message.content)
    loadingSummary[idx] = false
    cache.set(hash, summaryResult[idx])
  }

  let chartModal: HTMLDialogElement
</script>

<main class="flex min-h-screen flex-col">
  <dialog bind:this={chartModal} class="modal">
    <div class="modal-box text-center">
      <h3 class="text-lg font-bold">Distribution by Topics</h3>
      <Chart />
    </div>
    <form method="dialog" class="modal-backdrop">
      <button>close</button>
    </form>
  </dialog>

  <div class="navbar bg-base-200 sticky top-0 z-10 flex justify-between shadow-md">
    <div>
      <a href="/" class="btn btn-ghost text-xl"
        ><img src={logo} alt="Logo" class="h-8" /> Research Radar</a
      >
    </div>
    <input
      type="text"
      placeholder="Search"
      class="input input-bordered w-full max-w-screen-sm rounded-full"
      bind:value={searchQuery}
    />
    <button class="btn btn-ghost" aria-label="Stats" on:click={() => chartModal.showModal()}>
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512" class="h-8">
        <path
          d="M160 80c0-26.5 21.5-48 48-48l32 0c26.5 0 48 21.5 48 48l0 352c0 26.5-21.5 48-48 48l-32 0c-26.5 0-48-21.5-48-48l0-352zM0 272c0-26.5 21.5-48 48-48l32 0c26.5 0 48 21.5 48 48l0 160c0 26.5-21.5 48-48 48l-32 0c-26.5 0-48-21.5-48-48L0 272zM368 96l32 0c26.5 0 48 21.5 48 48l0 288c0 26.5-21.5 48-48 48l-32 0c-26.5 0-48-21.5-48-48l0-288c0-26.5 21.5-48 48-48z"
        />
      </svg>
    </button>
  </div>

  <div class="flex flex-1">
    <!-- Sidebar -->
    <div class="bg-base-300 flex flex-col gap-y-4 p-4">
      <div class="flex flex-col gap-y-2">
        <h3 class="text-base font-bold">Topics</h3>
        <div class="flex flex-col gap-y-2">
          {#each topicOptions as topic}
            <div class="flex items-center gap-x-2">
              <input
                type="checkbox"
                id={topic}
                class="checkbox"
                checked={selectedTopics.has(topic)}
                on:change={() => toggleTopic(topic)}
              />
              <label for={topic}>{topic}</label>
            </div>
          {/each}
        </div>
      </div>

      <div class="flex flex-col gap-y-2">
        <label for="dropdown" class="text-base font-bold">Summary Model</label>
        <select id="dropdown" class="select select-bordered w-full" bind:value={selectedModel}>
          {#each modelOptions as option}
            <option value={option}>{option}</option>
          {/each}
        </select>
      </div>
    </div>

    <!-- Main -->
    <div class="my-8 flex w-full justify-center">
      <div class="mx-4 flex w-full max-w-screen-md flex-col gap-y-4">
        {#if searchResults.length > 0}
          {#each searchResults as paper, idx}
            <div class="card rounded-lg bg-neutral-50 p-4 shadow-md">
              <a href={paper.paperlink || paper.link} class="text-lg font-bold">{paper.title}</a>
              <p class="line-clamp-1 text-sm text-gray-600">{paper.authors}</p>

              <p
                class="mt-2 overflow-hidden text-gray-700 transition-all"
                class:line-clamp-2={!expanded[idx]}
                title={paper.abstract}
              >
                {paper.abstract}
              </p>

              <div class="mt-4 flex justify-between">
                <button class="flex gap-x-2" on:click={() => toggleExpand(idx)}>
                  {#if expanded[idx]}
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 448 512"
                      class="mt-1.5 h-3 w-3"
                    >
                      <path
                        d="M246.6 41.4c-12.5-12.5-32.8-12.5-45.3 0l-160 160c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0L224 109.3 361.4 246.6c12.5 12.5 32.8 12.5 45.3 0s12.5-32.8 0-45.3l-160-160zm160 352l-160-160c-12.5-12.5-32.8-12.5-45.3 0l-160 160c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0L224 301.3 361.4 438.6c12.5 12.5 32.8 12.5 45.3 0s12.5-32.8 0-45.3z"
                      />
                    </svg>
                    Show Less
                  {:else}
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 448 512"
                      class="mt-1.5 h-3 w-3"
                    >
                      <path
                        d="M246.6 470.6c-12.5 12.5-32.8 12.5-45.3 0l-160-160c-12.5-12.5-12.5-32.8 0-45.3s32.8-12.5 45.3 0L224 402.7 361.4 265.4c12.5-12.5 32.8-12.5 45.3 0s12.5 32.8 0 45.3l-160 160zm160-352l-160 160c-12.5 12.5-32.8 12.5-45.3 0l-160-160c-12.5-12.5-12.5-32.8 0-45.3s32.8-12.5 45.3 0L224 210.7 361.4 73.4c12.5-12.5 32.8-12.5 45.3 0s12.5 32.8 0 45.3z"
                      />
                    </svg>
                    Show More
                  {/if}
                </button>

                {#if paperAvailable[idx]}
                  <button class="flex" on:click={() => summarize(idx)}>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      xmlns:xlink="http://www.w3.org/1999/xlink"
                      version="1.1"
                      class="mt-1 h-4 w-6"
                      viewBox="-0.5 -0.5 181 131"
                      ><defs /><g
                        ><g data-cell-id="0"
                          ><g data-cell-id="1"
                            ><g data-cell-id="NSrMD8DYlHj_BrsU8zd--6"
                              ><g
                                ><path
                                  d="M 30 30 L 30 80 Q 30 100 50 100 L 108.06 100"
                                  fill="none"
                                  stroke="rgb(0, 0, 0)"
                                  stroke-width="8"
                                  stroke-linejoin="round"
                                  stroke-linecap="round"
                                  stroke-miterlimit="10"
                                  pointer-events="stroke"
                                /><path
                                  d="M 141.06 100 L 108.06 116.5 L 108.06 83.5 Z"
                                  fill="rgb(0, 0, 0)"
                                  stroke="rgb(0, 0, 0)"
                                  stroke-width="8"
                                  stroke-linejoin="round"
                                  stroke-linecap="round"
                                  stroke-miterlimit="10"
                                  pointer-events="all"
                                /></g
                              ></g
                            ><g data-cell-id="NSrMD8DYlHj_BrsU8zd--8"
                              ><g
                                ><path
                                  d="M 50 80 L 100 80"
                                  fill="none"
                                  stroke="rgb(0, 0, 0)"
                                  stroke-width="6"
                                  stroke-linecap="round"
                                  stroke-miterlimit="10"
                                  pointer-events="stroke"
                                /></g
                              ></g
                            ><g data-cell-id="NSrMD8DYlHj_BrsU8zd--9"
                              ><g
                                ><path
                                  d="M 50 60 L 120 60"
                                  fill="none"
                                  stroke="rgb(0, 0, 0)"
                                  stroke-width="6"
                                  stroke-linecap="round"
                                  stroke-miterlimit="10"
                                  pointer-events="stroke"
                                /></g
                              ></g
                            ><g data-cell-id="NSrMD8DYlHj_BrsU8zd--10"
                              ><g
                                ><path
                                  d="M 50 40 L 140 40"
                                  fill="none"
                                  stroke="rgb(0, 0, 0)"
                                  stroke-width="6"
                                  stroke-linecap="round"
                                  stroke-miterlimit="10"
                                  pointer-events="stroke"
                                /></g
                              ></g
                            ></g
                          ></g
                        ></g
                      >
                    </svg>
                    Summarize
                  </button>
                {/if}
              </div>
            </div>

            {#if loadingSummary[idx] || summaryResult[idx]}
              <div class="card rounded-lg p-4">
                {#if loadingSummary[idx]}
                  <div class="w-full animate-pulse space-y-4">
                    <div class="h-2 w-full rounded bg-slate-600"></div>
                    <div class="h-2 w-11/12 rounded bg-slate-600"></div>
                    <div class="h-2 w-10/12 rounded bg-slate-600"></div>
                  </div>
                {:else if summaryResult[idx]}
                  <p
                    class="text-gray-700"
                    bind:innerHTML={summaryResult[idx]}
                    contenteditable="false"
                  ></p>
                {/if}
              </div>
            {/if}
          {/each}
        {:else}
          <p class="text-center text-gray-600">No results found</p>
        {/if}
      </div>
    </div>
  </div>

  <footer class="bg-base-200 py-2 text-center text-gray-700 shadow-inner">
    <p>&copy; 2024 Research Radar</p>
  </footer>
</main>
