"""Public error types returned by the catalog and part factories."""


class CadPartsError(Exception):
    """Base class for all library-specific errors."""


class UnknownFamilyError(CadPartsError, KeyError):
    """Raised when a requested family or alias is not registered."""


class InvalidParameterError(CadPartsError, ValueError):
    """Raised when a family receives an invalid engineering parameter."""
