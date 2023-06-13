import sys
from typing import List, Optional

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, Operator
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter

if sys.version_info >= (3, 9):
    from zoneinfo import ZoneInfo
else:
    from backports.zoneinfo import ZoneInfo

from forestadmin.datasource_toolkit.exceptions import ForestException, ForestValidationException
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.validations.field import FieldValidator


class ValidationMixin:
    def __init__(self, *args, **kwargs) -> None:
        super(ValidationMixin, self).__init__(*args, **kwargs)
        self.validations = {}

    def add_validation(self, name: str, validation: List):
        FieldValidator.validate(self.child_collection, name)

        field = self.child_collection.schema["fields"].get(name)
        if field is not None and field["type"] != FieldType.COLUMN:
            raise ForestException("Cannot add validators on a relation, use the foreign key instead")

        if field is not None and field["is_read_only"] is True:
            raise ForestException("Cannot add validators on a readonly field")

        if self.validations.get(name) is None:
            self.validations[name] = []
        self.validations[name].append(validation)

        self.mark_schema_as_dirty()

    async def create(self, caller: User, data: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        for record in data:
            self.__validate(record, caller.timezone, True)

        return super(ValidationMixin, self).create(caller, data)

    async def update(self, caller: User, filter: Optional[Filter], patch: RecordsDataAlias) -> None:
        self.__validate(patch, caller.timezone, False)

        return super(ValidationMixin, self).update(caller, filter, patch)

    def _refine_schema(self) -> CollectionSchema:
        schema: CollectionSchema = super(ValidationMixin, self)._refine_schema()

        for name, rules in self.validations.items():
            field = schema["fields"][name]
            if field.get("validations") is not None:
                field["validations"] = []
            field["validations"].extend(rules)

            schema["fields"][name] = field
        return schema

    def __validate(self, record: RecordsDataAlias, timezone: ZoneInfo, all_fields: bool):
        for name, rules in self.validations.items():
            if all_fields is True or record.get(name) is not None:
                # When setting a field to null, only the "Present" validator is relevant
                if record.get(name) is None:
                    applicable_rules = [*filter(lambda x: x["operator"] == Operator.PRESENT, rules)]
                else:
                    applicable_rules = rules

                for validator in applicable_rules:
                    raw_leaf = {"field": name}
                    raw_leaf.update(validator)
                    tree = ConditionTreeFactory.from_plain_object(raw_leaf)
                    if not tree.match(record, self, timezone):
                        message = f"{name} failed validation rule:"

                        if validator.get("value") is not None:
                            value = (
                                ",".join(validator["value"])
                                if isinstance(validator["value"], list)
                                else validator["value"]
                            )
                            rule = f"{validator['operator']}({value})"
                        else:
                            rule = validator["operator"]

                        raise ForestValidationException(f"{message} '{rule}'")
