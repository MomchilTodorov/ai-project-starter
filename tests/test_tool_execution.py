import pytest

import tool_execution
from tool_execution import ToolExecutionError, execute_tool_call


def test_approved_call_returns_product():
    result = execute_tool_call("get_product", {"product_id": 123})

    assert result["id"] == 123
    assert result["name"] == "Wireless Mouse"


def test_unapproved_function_is_rejected():
    with pytest.raises(ValueError, match="Unapproved function"):
        execute_tool_call("delete_product", {"product_id": 123})


@pytest.mark.parametrize("args", [None, [], {}, {"product_id": 123, "extra": True}])
def test_call_requires_one_named_argument(args):
    with pytest.raises(ValueError, match="Expected a single product_id argument"):
        execute_tool_call("get_product", args)


@pytest.mark.parametrize("product_id", ["123", 123.0, True, 0, -1])
def test_product_id_must_be_a_positive_integer(product_id):
    with pytest.raises(ValueError, match="Invalid product ID"):
        execute_tool_call("get_product", {"product_id": product_id})


def test_missing_product_returns_catalog_result():
    result = execute_tool_call("get_product", {"product_id": 999})

    assert result == {"error": "Product not found"}


def test_lookup_exception_becomes_tool_execution_error(monkeypatch):
    def broken_lookup(product_id):
        raise OSError("Catalog unavailable")

    monkeypatch.setattr(tool_execution, "get_product", broken_lookup)

    with pytest.raises(ToolExecutionError, match="^Product lookup failed$"):
        execute_tool_call("get_product", {"product_id": 123})

def test_out_of_stock_product_is_returned():
    result = execute_tool_call("get_product", {"product_id": 125})

    assert result["id"] == 125
    assert result["stock"] == 0