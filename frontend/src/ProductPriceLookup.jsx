import { useState } from 'react'
import { getProductPrice } from './api'

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
      <form onSubmit={handleSubmit}>
        <input
          id="catalog-product-id"
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