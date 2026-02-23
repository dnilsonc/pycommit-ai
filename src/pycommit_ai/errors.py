class KnownError(Exception):
    """Exception raised for known errors that should be displayed nicely to the user."""
    pass

class AIServiceError(Exception):
    """Exception raised for errors occurring within AI service providers."""
    
    def __init__(
        self, 
        message: str, 
        status: int | None = None, 
        code: str | None = None, 
        content: str | None = None, 
        original_error: Exception | None = None
    ):
        super().__init__(message)
        self.status = status
        self.code = code
        self.content = content
        self.original_error = original_error
