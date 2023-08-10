from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.exceptions import ForbiddenError, ForestValidationException, UnprocessableError


class HookContext(CollectionCustomizationContext):
    def throw_validation_error(self, message: str):
        raise ForestValidationException(message)

    def throw_forbidden_error(self, message: str):
        raise ForbiddenError(message)

    def throw_error(self, message: str):
        raise UnprocessableError(message)
