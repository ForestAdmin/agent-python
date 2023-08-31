from typing import Any, Dict, Optional


class ForestException(Exception):
    def __init__(self, message: str = "", *args: object) -> None:
        super().__init__(f"🌳🌳🌳{message}", *args)


class DatasourceToolkitException(ForestException):
    pass


class BusinessError(DatasourceToolkitException):
    def __init__(
        self,
        message: str = "",
        headers: Optional[Dict[str, Any]] = None,
        name: str = "ValidationError",
        data: Optional[Dict[str, Any]] = {},
        *args: object,
    ) -> None:
        self.headers = headers
        self.data = data
        self.name = name
        super().__init__(message, *args)


class ValidationError(BusinessError):
    def __init__(
        self,
        message: str = "",
        headers: Optional[Dict[str, Any]] = None,
        name: str = "ValidationError",
        data: Optional[Dict[str, Any]] = {},
        *args: object,
    ) -> None:
        super().__init__(message, headers, name, data, *args)


class ForbiddenError(BusinessError):
    def __init__(
        self,
        message: str = "",
        headers: Optional[Dict[str, Any]] = None,
        name: str = "ForbiddenError",
        data: Optional[Dict[str, Any]] = {},
        *args: object,
    ) -> None:
        super().__init__(message, headers, name, data, *args)


class UnprocessableError(BusinessError):
    def __init__(
        self,
        message: str = "",
        headers: Optional[Dict[str, Any]] = None,
        name: str = "UnprocessableError",
        data: Optional[Dict[str, Any]] = {},
        *args: object,
    ) -> None:
        super().__init__(message, headers, name, data, *args)


class ConflictError(BusinessError):
    def __init__(
        self,
        message: str = "",
        headers: Optional[Dict[str, Any]] = None,
        name: str = "ConflictError",
        data: Optional[Dict[str, Any]] = {},
        *args: object,
    ) -> None:
        super().__init__(message, headers, name, data, *args)


class RequireApproval(ForbiddenError):
    def __init__(
        self,
        message: str = "",
        headers: Optional[Dict[str, Any]] = None,
        name: str = "RequireApproval",
        data: Optional[Dict[str, Any]] = {},
        *args: object,
    ) -> None:
        super().__init__(message, headers, name, data, *args)
