class WrongSignature(Exception):
    """Raises when a received message has wrong signature."""


class DuplicateUnit(Exception):
    """Raises when id of a unit already exists in the database."""
