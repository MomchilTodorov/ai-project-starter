import { useState } from 'react'
import { askStorePolicy } from './api'

const exampleQuestions = [
  'Can I send an unused item back?',
  'How soon will my package get here?',
]

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
      <p className="tool-description" id="policy-description">
        Python finds the relevant policy. Gemini answers from that text. You’ll see the policy name below the answer.
      </p>
      <div className="tool-examples" role="group" aria-label="Example policy questions">
        {exampleQuestions.map(example => (
          <button
            key={example}
            type="button"
            disabled={loading}
            onClick={() => {
              setQuestion(example)
              setResult(null)
            }}
          >
            {example}
          </button>
        ))}
      </div>
      <form onSubmit={handleSubmit}>
        <input
          id="policy-question"
          aria-describedby="policy-description"
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
