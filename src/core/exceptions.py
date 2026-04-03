class ApplicationError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(f"ApplicationError: {message}")