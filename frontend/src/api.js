
const API_BASE = '/api'

// Create a new conversation
export async function createConversation() {
  const response = await fetch(`${API_BASE}/conversations`, {
    method: 'POST'
  })

  if (!response.ok) {
    throw new Error('Could not create conversation')
  }

  return response.json()
}

// Load saved messages
export async function getMessages(conversationId) {
  const response = await fetch(
    `${API_BASE}/conversations/${conversationId}/messages`
  )

  if (!response.ok) {
    throw new Error('Could not load conversation')
  }

  const data = await response.json()
  return data.messages
}

// Stream a new AI response
export async function* streamMessage(message, conversationId) {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message,
      conversation_id: conversationId
    })
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

    throw new Error('Stream ended unexpectedly')
  } finally {
    await reader.cancel()
    reader.releaseLock()
  }
}

export async function getConversations() {
  const response = await fetch('/api/conversations')

  if (!response.ok) {
    throw new Error('Could not load conversations')
  }

  const data = await response.json()

  return data.conversations
}
