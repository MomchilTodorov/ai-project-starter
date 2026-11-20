import { useEffect, useRef, useState } from 'react'
import { streamMessage } from './api'
import './App.css'

function App() {
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)

  const messagesEndRef = useRef(null)

  // Scroll down whenever messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: 'auto',
      block: 'end'
    })
  }, [messages])

  async function handleSubmit(event) {
    event.preventDefault()

    if (!message.trim() || loading) return

    const userMessage = message.trim()

    // Save previous conversation history
    const history = messages
      .filter(item =>
        item.role === 'user' || item.role === 'assistant'
      )
      .slice(-20)

    // Add the user message and an empty AI message
    setMessages(prev => [
      ...prev,
      { role: 'user', text: userMessage },
      { role: 'assistant', text: '' }
    ])

    setMessage('')
    setLoading(true)

    try {
      for await (const chunk of streamMessage(userMessage, history)) {
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

      setMessages(prev => {
        const updated = [...prev]

        // Remove any incomplete AI answer
        updated.pop()

        return [
          ...updated,
          {
            role: 'error',
            text: error.message || 'Something went wrong.'
          }
        ]
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="chat-container">
      <h1>AI Project Starter</h1>
      <p className="subtitle">My first AI application</p>

      <div className="messages">
        {messages.length === 0 && (
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
          disabled={loading}
        />

        <button type="submit" disabled={loading}>
          {loading ? 'Thinking...' : 'Send'}
        </button>
      </form>
    </main>
  )
}

export default App
