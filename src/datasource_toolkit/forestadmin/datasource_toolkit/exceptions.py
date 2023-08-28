from typing import Any, Dict, Optional


class ForestException(Exception):
    def __init__(self, message: str = "", *args: object) -> None:
        super().__init__(f"🌳🌳🌳{message}", *args)


class DatasourceToolkitException(ForestException):
    pass


class BusinessError(DatasourceToolkitException):
    def __init__(self, message: str = "", data: Optional[Dict[str, Any]] = None, name: str = "", *args: object) -> None:
        self.data = data
        self.name = name
        super().__init__(message, *args)


class ValidationError(BusinessError):
    def __init__(
        self, message: str = "", data: Optional[Dict[str, Any]] = None, name: str = "ValidationError", *args: object
    ) -> None:
        super().__init__(message, data, name, *args)

    pass


class ForbiddenError(BusinessError):
    def __init__(
        self, message: str = "", data: Optional[Dict[str, Any]] = None, name: str = "ForbiddenError", *args: object
    ) -> None:
        super().__init__(message, data, name, *args)


class UnprocessableError(BusinessError):
    def __init__(
        self, message: str = "", data: Optional[Dict[str, Any]] = None, name: str = "UnprocessableError", *args: object
    ) -> None:
        super().__init__(message, data, name, *args)


class ConflictError(BusinessError):
    def __init__(
        self, message: str = "", data: Optional[Dict[str, Any]] = None, name: str = "ConflictError", *args: object
    ) -> None:
        super().__init__(message, data, name, *args)


class RequireApproval(ForbiddenError):
    def __init__(
        self, message: str = "", data: Optional[Dict[str, Any]] = None, name: str = "RequireApproval", *args: object
    ) -> None:
        super().__init__(message, data, name, *args)
