import { useEffect, useRef, useState } from 'react'
import {
  createConversation,
  getMessages,
  streamMessage
} from './api'
import './App.css'

function App() {
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState([])
  const [conversationId, setConversationId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [initializing, setInitializing] = useState(true)
  const [startupError, setStartupError] = useState('')

  const messagesEndRef = useRef(null)
  const initializedRef = useRef(false)

  // Load or create a conversation on startup
  useEffect(() => {
    if (initializedRef.current) return
    initializedRef.current = true

    async function initializeChat() {
      try {
        const savedId = localStorage.getItem('conversation_id')

        if (savedId) {
          try {
            const saved = await getMessages(savedId)

            setConversationId(Number(savedId))
            setMessages(saved.map(item => ({
              role: item.role,
              text: item.content
            })))

            return
          } catch (error) {
            console.warn('Could not restore chat:', error)
          }
        }

        const conversation = await createConversation()

        localStorage.setItem(
          'conversation_id',
          String(conversation.id)
        )

        setConversationId(conversation.id)
      } catch (error) {
        console.error(error)
        setStartupError('Could not initialize conversation.')
      } finally {
        setInitializing(false)
      }
    }

    initializeChat()
  }, [])

  // Scroll to the latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: 'auto',
      block: 'end'
    })
  }, [messages])

  async function handleSubmit(event) {
    event.preventDefault()

    if (!message.trim() || loading || !conversationId) return

    const userMessage = message.trim()

    setMessages(prev => [
      ...prev,
      { role: 'user', text: userMessage },
      { role: 'assistant', text: '' }
    ])

    setMessage('')
    setLoading(true)

    try {
      for await (const chunk of streamMessage(
        userMessage,
        conversationId
      )) {
        setMessages(prev => {
          const updated = [...prev]
          const lastIndex = updated.length - 1

          updated[lastIndex] = {
            ...updated[lastIndex],
            text: updated[lastIndex].text + chunk
          }

          return updated
        })
      }
    } catch (error) {
      console.error(error)

      // Reload the database state after a failed stream
      try {
        const saved = await getMessages(conversationId)

        setMessages([
          ...saved.map(item => ({
            role: item.role,
            text: item.content
          })),
          {
            role: 'error',
            text: error.message || 'Something went wrong.'
          }
        ])
      } catch {
        setMessages(prev => [
          ...prev,
          {
            role: 'error',
            text: 'Could not reload conversation.'
          }
        ])
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="chat-container">
      <h1>AI Project Starter</h1>
      <p className="subtitle">My first AI application</p>

      <div className="messages">
        {initializing && <p>Loading conversation...</p>}

        {startupError && (
          <p className="message error">{startupError}</p>
        )}

        {!initializing && !startupError &&
          messages.length === 0 && (
            <p className="empty">Ask me anything!</p>
          )}

        {messages.map((item, index) => (
          <div
            key={index}
            className={`message ${item.role}`}
          >
            {item.text || (
              <span className="loading">Thinking...</span>
            )}
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={message}
          onChange={e => setMessage(e.target.value)}
          placeholder="Type your message..."
          disabled={loading || initializing || !conversationId}
        />

        <button
          type="submit"
          disabled={loading || initializing || !conversationId}
        >
          {loading ? 'Thinking...' : 'Send'}
        </button>
      </form>
    </main>
  )
}

export default App
