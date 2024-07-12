from typing import List, Literal, Optional, Union

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.decorators.write.write_replace.types import WriteDefinition
from forestadmin.datasource_toolkit.decorators.write.write_replace.write_customization_context import (
    WriteCustomizationContext,
)
from forestadmin.datasource_toolkit.exceptions import ForestException
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.fields import FieldType
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema, Datasource
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.utils.user_callable import call_user_function
from forestadmin.datasource_toolkit.validations.field import FieldValidator
from forestadmin.datasource_toolkit.validations.records import RecordValidator


class WriteReplaceCollection(CollectionDecorator):
    def __init__(self, collection: Collection, datasource: Datasource):
        super().__init__(collection, datasource)
        self._handlers = {}

    def replace_field_writing(self, field_name: str, definition: WriteDefinition):
        FieldValidator.validate(self, field_name)

        if not definition:
            raise ForestException("A new writing method should be provided to replace field writing")

        self._handlers[field_name] = definition
        self.mark_schema_as_dirty()

    def _refine_schema(self, sub_schema: CollectionSchema) -> CollectionSchema:
        schema = {**sub_schema, "fields": sub_schema["fields"]}

        for field_name, handler in self._handlers.items():
            schema["fields"][field_name] = {**schema["fields"][field_name], "is_read_only": handler is None}

        return schema

    async def create(self, caller: User, data: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        new_records = []
        for record in data:
            new_records.append(await self._rewrite_patch(caller, "create", record))

        return await self.child_collection.create(caller, new_records)

    async def update(self, caller: User, _filter: Optional[Filter], patch: RecordsDataAlias):
        new_patch = await self._rewrite_patch(caller, "update", patch, [], _filter)

        return await self.child_collection.update(caller, _filter, new_patch)

    async def _rewrite_patch(
        self,
        caller: User,
        action: Union[Literal["create"], Literal["update"]],
        patch: RecordsDataAlias,
        used_handlers: List[str] = None,
        filter_: Optional[Filter] = None,
    ) -> RecordsDataAlias:
        """Takes a patch and recursively applies all rewriting rules to it."""
        if used_handlers is None:
            used_handlers = list()

        # We rewrite the patch by applying all handlers on each field.
        context = WriteCustomizationContext(self, caller, action, patch, filter_)
        patches = []  # map(lambda key: self._rewrite_key(context, key, used_handlers), patch.keys())
        for key in patch.keys():
            patches.append(await self._rewrite_key(context, key, used_handlers))

        # We now have a list of patches (one per field) that we can merge.
        new_patch = self._deep_merge(*patches)

        # Check that the customer handlers did not introduce invalid data.
        if len(new_patch.keys()) > 0:
            RecordValidator.validate(self, new_patch)

        return new_patch

    async def _rewrite_key(self, context: WriteCustomizationContext, key: str, used: List[str]) -> RecordsDataAlias:
        # Guard against infinite recursion.
        if key in used:
            raise ForestException(f"Cycle detected: {' -> '.join(used)}.")

        field_schema = self.schema["fields"].get(key, {})

        # Handle Column fields.
        if field_schema.get("type") == FieldType.COLUMN:
            # We either call the customer handler or a default one that does nothing.
            handler = self._handlers.get(key, lambda value, context: {key: value})
            field_patch = await call_user_function(handler, context.record[key], context)
            if field_patch is None:
                field_patch: RecordsDataAlias = {}

            if not isinstance(field_patch, dict):
                raise ForestException(f"The write handler of {key} should return an object or nothing.")

            # Isolate change to our own value (which should not recurse) and the rest which should
            # trigger the other handlers.
            if key in field_patch:
                value = field_patch.pop(key)
                is_value = True
            else:
                value = None
                is_value = False

            new_patch = await self._rewrite_patch(context.caller, context.action, field_patch, [*used, key])

            if is_value:
                return self._deep_merge({key: value}, new_patch)
            else:
                return new_patch

        # Handle relation fields.
        if field_schema.get("type") in [FieldType.MANY_TO_ONE, FieldType.ONE_TO_ONE]:
            # Delegate relations to the appropriate collection.
            relation = self.datasource.get_collection(field_schema["foreign_collection"])
            return {key: await relation._rewrite_patch(context.caller, context.action, context.record[key])}

        raise ForestException(f"Unknown field : {key}")

    def _deep_merge(self, *patches: List[RecordsDataAlias]) -> RecordsDataAlias:
        """Recursively merge patches into a single one ensuring that there is no conflict."""
        acc = {}
        for patch in patches:
            for key, value in patch.items():
                # We could check that this is a relation field but we choose to only check for objects
                # to allow customers to use this for JSON fields.
                if acc.get(key) is None:
                    acc[key] = value
                elif isinstance(acc[key], dict):
                    acc[key] = self._deep_merge(acc[key], value)
                else:
                    raise ForestException(f"Conflict value on the field {key}. It received several values.")
        return acc
