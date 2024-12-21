class SECDataAppBaseException(Exception):
    """Base exception for SEC Data Application."""
    pass

class APIConnectionError(SECDataAppBaseException):
    """Raised when there's an issue connecting to an external API."""
    pass

class DataRetrievalError(SECDataAppBaseException):
    """Raised when data retrieval fails."""
    pass

class DataParsingError(SECDataAppBaseException):
    """Raised when parsing of retrieved data fails."""
    pass

class CacheError(SECDataAppBaseException):
    """Raised when cache-related operations fail."""
    pass

class ConfigurationError(SECDataAppBaseException):
    """Raised when configuration is invalid or missing."""
    pass
