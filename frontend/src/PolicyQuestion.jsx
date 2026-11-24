import { useState } from 'react'
import { askStorePolicy } from './api'

export default function PolicyQuestion() {
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    const trimmedQuestion = question.trim()
    if (!trimmedQuestion || loading) return

    setLoading(true)
    setResult(null)

    try {
      setResult(await askStorePolicy(trimmedQuestion))
    } catch (error) {
      setResult({ answer: error.message || 'Could not load a policy answer.', source: null })
    } finally {
      setLoading(false)
    }
  }

  return (
    <section aria-label="Store policy lookup">
      <label htmlFor="policy-question">Store policy question</label>
      <form onSubmit={handleSubmit}>
        <input
          id="policy-question"
          placeholder="Can I send an unused item back?"
          value={question}
          onChange={event => setQuestion(event.target.value)}
          maxLength={10000}
          disabled={loading}
          required
        />
        <button type="submit" disabled={loading || !question.trim()}>
          {loading ? 'Looking up…' : 'Ask about policies'}
        </button>
      </form>
      <div role="status">
        {result && <p>{result.answer}</p>}
        {result?.source && <p><small>Source: {result.source}</small></p>}
      </div>
    </section>
  )
}
