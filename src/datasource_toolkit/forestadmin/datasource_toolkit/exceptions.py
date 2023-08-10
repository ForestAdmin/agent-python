from typing import Any, Dict, Optional


class ForestException(Exception):
    def __init__(self, message: str = "", *args: object) -> None:
        super().__init__(f"🌳🌳🌳{message}", *args)


class DatasourceToolkitException(ForestException):
    pass


class BusinessError(DatasourceToolkitException):
    def __init__(self, message: str = "", data: Optional[Dict[str, Any]] = None, *args: object) -> None:
        self.data = data
        super().__init__(message, *args)


class ForestValidationException(BusinessError):
    pass


class ForbiddenError(BusinessError):
    pass


class UnprocessableError(BusinessError):
    pass
