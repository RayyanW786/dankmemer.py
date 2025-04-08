class Fuzzy:
    """
    Represents a fuzzy match criterion.

    :param value: The string value to match.
    :param cutoff: The minimum matching ratio (0-100) required for a successful fuzzy match.
                   Defaults to 80.
    """

    def __init__(self, value: str, cutoff: int = 80) -> None:
        self.value: str = value
        self.cutoff: int = cutoff

    def __repr__(self) -> str:
        return f"Fuzzy({self.value!r}, cutoff={self.cutoff})"
