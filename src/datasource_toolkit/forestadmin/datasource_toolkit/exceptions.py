class ForestException(Exception):
    def __init__(self, message: str = "", *args: object) -> None:
        super().__init__(f"🌳🌳🌳{message}", *args)


class DatasourceToolkitException(ForestException):
    pass


class BusinessError(ForestException):
    pass


class ForestValidationException(BusinessError):
    pass


class ForbiddenError(BusinessError):
    pass
