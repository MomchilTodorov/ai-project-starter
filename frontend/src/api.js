const API_URL = '/api/chat'

export async function* streamMessage(message, history = []) {
  const response = await fetch(API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ message, history })
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }

  if (!response.body) {
    throw new Error('Streaming is not supported')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()

  let buffer = ''

  try {
    while (true) {
      const { value, done } = await reader.read()

      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const events = buffer.split('\n\n')
      buffer = events.pop()

      for (const event of events) {
        const dataLine = event
          .split('\n')
          .find(line => line.startsWith('data: '))

        if (!dataLine) continue

        const data = JSON.parse(dataLine.slice(6))

        if (data.type === 'error') {
          throw new Error(data.message)
        }

        if (data.type === 'done') {
          return
        }

        if (data.type === 'chunk') {
          yield data.text
        }
      }
    }

    throw new Error('The AI stream ended unexpectedly')
  } finally {
    await reader.cancel()
    reader.releaseLock()
  }
}
