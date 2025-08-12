def test_function(x: str) -> int:
    return x  # Type error: returning str instead of int

def missing_type(x):  # Missing type annotation
    return x

def wrong_return() -> str:
    return 42  # Type error: returning int instead of str
