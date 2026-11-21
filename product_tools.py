
# Sample product data for learning purposes
PRODUCTS = {
    123: {
        "id": 123,
        "name": "Wireless Mouse",
        "price": 29.99,
        "currency": "EUR",
        "stock": 15
    },
    124: {
        "id": 124,
        "name": "Mechanical Keyboard",
        "price": 89.99,
        "currency": "EUR",
        "stock": 8
    },
    125: {
        "id": 125,
        "name": "USB-C Hub",
        "price": 39.99,
        "currency": "EUR",
        "stock": 0
    }
}


def get_product(product_id: int) -> dict:
    """Get product information by its unique ID.

    Args:
        product_id: The numeric ID of the product to retrieve.
    """
    print(f"[TOOL] get_product called with ID: {product_id}")

    product = PRODUCTS.get(product_id)

    if product is None:
        return {"error": "Product not found"}

    return product
