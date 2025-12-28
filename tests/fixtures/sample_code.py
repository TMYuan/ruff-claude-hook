"""Sample valid Python code for testing."""


def calculate_average(numbers):
    """Calculate the average of a list of numbers.

    Args:
        numbers: List of numeric values

    Returns:
        Average value

    Raises:
        ValueError: If numbers list is empty
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    return sum(numbers) / len(numbers)


def format_greeting(name, title=None):
    """Format a greeting message.

    Args:
        name: Person's name
        title: Optional title (e.g., 'Dr.', 'Prof.')

    Returns:
        Formatted greeting string
    """
    if title:
        return f"Hello, {title} {name}!"
    return f"Hello, {name}!"


class DataProcessor:
    """Process and validate data."""

    def __init__(self, data):
        """Initialize processor.

        Args:
            data: Data to process
        """
        self.data = data
        self.processed = False

    def process(self):
        """Process the data."""
        if self.processed:
            return self.data

        # Simple processing logic
        self.data = [item.strip() if isinstance(item, str) else item
                     for item in self.data]
        self.processed = True
        return self.data

    def reset(self):
        """Reset processing state."""
        self.processed = False
