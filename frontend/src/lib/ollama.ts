import { Ollama } from 'ollama'

const ollama = new Ollama({ host: import.meta.env.VITE_OLLAMA_URL })

export async function getChat(text: string, model: string) {
  const message = {
    role: 'user',
    content: `Summarize:\n${text}`
  }

  const response = await ollama.chat({
    model: model,
    messages: [message],
    // stream: true,
    options: {
      num_ctx: import.meta.env.VITE_OLLAMA_NUM_CTX || 4096
    }
  })

  return response
}
