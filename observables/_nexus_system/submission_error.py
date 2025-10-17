from typing import Any, Optional


class SubmissionError(ValueError):
    """Exception raised when a value cannot be accepted for submission."""
    
    def __init__(self, message: str, value: Any, key: Optional[str] = None):
        """
        Args:
            message: The message to display
            value: The value that caused the error
            key: The key that caused the error
        """

        self.value = value
        self.key = key
        
        if key is not None:
            full_message = f"Cannot accept value {value} for submission to key {key}: {message}"
        else:
            full_message = f"Cannot accept value {value} for submission: {message}"
        
        super().__init__(full_message)
