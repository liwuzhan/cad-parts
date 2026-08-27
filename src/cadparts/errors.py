"""Public error types returned by the catalog and part factories."""


class CadPartsError(Exception):
    """Base class for all library-specific errors."""


class UnknownFamilyError(CadPartsError, KeyError):
    """Raised when a requested family or alias is not registered."""


class InvalidParameterError(CadPartsError, ValueError):
    """Raised when a family receives an invalid engineering parameter."""


class CatalogDataError(CadPartsError, ValueError):
    """Raised when a model-facing catalog declaration is invalid or stale."""


class UnknownPartError(CadPartsError, KeyError):
    """Raised when a catalog item or alias cannot be resolved."""


class ReviewError(CadPartsError, RuntimeError):
    """Raised when an artifact or multimodal review cannot be completed."""
