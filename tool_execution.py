from collections.abc import Mapping

from product_tools import get_product


class ToolExecutionError(RuntimeError):
    """An approved tool failed during execution."""


def execute_tool_call(name: str | None, args: object) -> dict:
    """Validate a manual tool request and return the product lookup result."""
    if name != "get_product":
        raise ValueError("Unapproved function")

    if not isinstance(args, Mapping) or args.keys() != {"product_id"}:
        raise ValueError("Expected a single product_id argument")

    product_id = args["product_id"]
    # bool is a subclass of int, so check the exact type.
    if type(product_id) is not int or product_id <= 0:
        raise ValueError("Invalid product ID")

    try:
        return get_product(product_id)
    except Exception as exc:
        raise ToolExecutionError("Product lookup failed") from exc
