# main.py
import random
from fastmcp import FastMCP

mcp = FastMCP("Simple Number Server")


@mcp.tool
def add_numbers(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


@mcp.tool
def random_number(minimum: int, maximum: int) -> int:
    """Generate a random integer between minimum and maximum, inclusive."""
    if minimum > maximum:
        raise ValueError("minimum must be less than or equal to maximum")
    return random.randint(minimum, maximum)


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)