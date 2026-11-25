import { useState } from 'react'
import { getProductPrice } from './api'

const exampleProducts = [
  { id: '123', name: 'Wireless Mouse' },
  { id: '124', name: 'Mechanical Keyboard' },
]

export default function ProductPriceLookup() {
  const [productId, setProductId] = useState('')
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setLoading(true)
    setStatus('')

    try {
      const product = await getProductPrice(productId)

      if (product === null) {
        setStatus('Product not found.')
        return
      }

      const price = `${product.price.toFixed(2)} ${product.currency}`
      setStatus(`Product ${product.product_id} costs ${price}.`)
    } catch {
      setStatus('Could not load the catalog price.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section aria-label="Catalog price lookup">
      <label htmlFor="catalog-product-id">Product ID</label>
      <p className="tool-description" id="catalog-description">
        Check price reads from the sample catalog. In chat, Gemini can ask the server to look up a price.
      </p>
      <div className="tool-examples" role="group" aria-label="Example products">
        {exampleProducts.map(({ id, name }) => (
          <button
            key={id}
            type="button"
            disabled={loading}
            onClick={() => {
              setProductId(id)
              setStatus('')
            }}
          >
            {name} ({id})
          </button>
        ))}
      </div>
      <form onSubmit={handleSubmit}>
        <input
          id="catalog-product-id"
          aria-describedby="catalog-description"
          type="text"
          inputMode="numeric"
          pattern="[1-9][0-9]*"
          required
          value={productId}
          onChange={event => setProductId(event.target.value)}
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Checking…' : 'Check price'}
        </button>
      </form>
      <p role="status">{status}</p>
    </section>
  )
}
