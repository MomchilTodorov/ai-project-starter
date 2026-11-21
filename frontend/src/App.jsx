import { useEffect, useRef, useState } from 'react'
import {
  createConversation,
  getConversations,
  getMessages,
  streamMessage
} from './api'
import './App.css'

function App() {
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState([])
  const [conversations, setConversations] = useState([])
  const [conversationId, setConversationId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [initializing, setInitializing] = useState(true)
  const [error, setError] = useState('')

  const messagesEndRef = useRef(null)
  const initializedRef = useRef(false)

  // Load existing conversations when the application starts
  useEffect(() => {
    if (initializedRef.current) return
    initializedRef.current = true

    async function initialize() {
      try {
        const chats = await getConversations()
        setConversations(chats)

        const savedId = Number(
          localStorage.getItem('conversation_id')
        )

        const existing = chats.find(chat => chat.id === savedId)

        if (existing) {
          const savedMessages = await getMessages(existing.id)

          setConversationId(existing.id)
          setMessages(savedMessages.map(item => ({
            role: item.role,
            text: item.content
          })))
        } else {
          const chat = await createConversation()

          setConversations(prev => [chat, ...prev])
          setConversationId(chat.id)

          localStorage.setItem(
            'conversation_id',
            String(chat.id)
          )
        }
      } catch (err) {
        console.error(err)
        setError('Could not initialize the application.')
      } finally {
        setInitializing(false)
      }
    }

    initialize()
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: 'auto',
      block: 'end'
    })
  }, [messages])

  async function handleNewChat() {
    if (loading || initializing) return

    setLoading(true)
    setError('')

    try {
      const chat = await createConversation()

      setConversations(prev => [chat, ...prev])
      setConversationId(chat.id)
      setMessages([])
      setMessage('')

      localStorage.setItem(
        'conversation_id',
        String(chat.id)
      )
    } catch (err) {
      console.error(err)
      setError('Could not create conversation.')
    } finally {
      setLoading(false)
    }
  }

  async function handleSelectChat(id) {
    if (loading || initializing || id === conversationId) return

    setLoading(true)
    setError('')

    try {
      const saved = await getMessages(id)

      setConversationId(id)
      setMessages(saved.map(item => ({
        role: item.role,
        text: item.content
      })))

      localStorage.setItem('conversation_id', String(id))
    } catch (err) {
      console.error(err)
      setError('Could not load conversation.')
    } finally {
      setLoading(false)
    }
  }

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
    setError('')

    try {
      for await (const chunk of streamMessage(
        userMessage,
        conversationId
      )) {
        setMessages(prev => {
          const updated = [...prev]
          const index = updated.length - 1

          updated[index] = {
            ...updated[index],
            text: updated[index].text + chunk
          }

          return updated
        })
      }
      const updatedConversations = await getConversations()
      setConversations(updatedConversations)
    } catch (err) {
      console.error(err)

      try {
        const saved = await getMessages(conversationId)

        setMessages([
          ...saved.map(item => ({
            role: item.role,
            text: item.content
          })),
          {
            role: 'error',
            text: err.message || 'AI service unavailable.'
          }
        ])
      } catch {
        setError('Could not restore conversation.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <h2>Conversations</h2>

        <button
          className="new-chat-btn"
          onClick={handleNewChat}
          disabled={loading || initializing}
        >
          + New Chat
        </button>

        <div className="conversation-list">
          {conversations.map(chat => (
            <button
              key={chat.id}
              className={`conversation-item ${
                chat.id === conversationId ? 'active' : ''
              }`}
              onClick={() => handleSelectChat(chat.id)}
              disabled={loading || initializing}
            >
              {chat.title} #{chat.id}
            </button>
          ))}
        </div>
      </aside>

      <main className="chat-container">
        <h1>AI Project Starter</h1>
        <p className="subtitle">My first AI application</p>

        {error && <p className="message error">{error}</p>}

        <div className="messages">
          {initializing && (
            <p className="empty">Loading conversations...</p>
          )}

          {!initializing && messages.length === 0 && (
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
    </div>
  )
}

export default App
