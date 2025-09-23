import functools
from typing import Any
from fastmcp import FastMCP

calculator = FastMCP("Calculator 🧮")


@calculator.tool
def add(a: int | float, b: int | float) -> int | float:
    """Add two numbers."""
    return a + b


@calculator.tool
def multiply(a: int | float, b: int | float) -> int | float:
    """Multiply some numbers."""
    return a * b


@calculator.tool
def divide(a: int | float, b: int | float) -> int | float:
    """Divide two numbers."""
    return a / b


@calculator.tool
def total(numbers: list[int | float]) -> int | float:
    """Add multiple numbers."""
    return sum(numbers)


@calculator.tool
def product(numbers: list[int | float]) -> int | float:
    """Multiply some numbers."""
    return functools.reduce(lambda x, y: x * y, numbers)


@calculator.tool
def average(numbers: list[int | float]) -> int | float:
    """Return the average of a sequence of numbers."""
    return sum(numbers) / len(numbers)


@calculator.tool
def count_string_occurences(some_text: str | Any, target: str) -> int:
    """Returns the number of times that the `target` string is found inside `some_string`."""
    return str(some_text).count(target)


def main():
    calculator.run()


if __name__ == "__main__":
    main()
