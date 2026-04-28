"""Calculator module with intentional issues for review testing."""

PI = 3.14


def add(a: int, b: int) -> int:
    return a + b


def divide(a, b):
    return a / b


def average(values=[]):
    total = 0
    for v in values:
        total += v
    return total / len(values)


def greet(name=None):
    try:
        if name == None:
            return "Hello, stranger!"
        return "Hello, " + name
    except:
        # bare except is bad practice
        return "Hello?"
