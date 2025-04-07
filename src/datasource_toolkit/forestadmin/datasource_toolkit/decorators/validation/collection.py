import sys
from typing import Dict, List, Optional

if sys.version_info >= (3, 9):
    from zoneinfo import ZoneInfo
else:
    from backports.zoneinfo import ZoneInfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.exceptions import ForestException, ValidationError
from forestadmin.datasource_toolkit.interfaces.fields import Operator, Validation
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.validations.field import FieldValidator


class ValidationCollectionDecorator(CollectionDecorator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validations: Dict[str, List[Validation]] = {}

    def add_validation(self, name: str, validation: Validation):
        FieldValidator.validate(self.child_collection, name)

        field = self.child_collection.schema["fields"][name]

        if field is not None and field.get("is_read_only", False) is True:
            raise ForestException("Cannot add validators on a readonly field")

        # cast
        validation["operator"] = Operator(validation["operator"])
        if self.validations.get(name) is None:
            self.validations[name] = []
        self.validations[name].append(validation)

        self.mark_schema_as_dirty()

    async def create(self, caller: User, data: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        for record in data:
            self.__validate(record, caller.timezone, True)

        return await super().create(caller, data)

    async def update(self, caller: User, filter: Optional[Filter], patch: RecordsDataAlias) -> None:
        self.__validate(patch, caller.timezone, False)

        return await super().update(caller, filter, patch)

    def _refine_schema(self, sub_schema: CollectionSchema) -> CollectionSchema:
        fields_schema = {**sub_schema["fields"]}
        for name, rules in self.validations.items():
            if fields_schema[name].get("validations") is None:
                fields_schema[name]["validations"] = []
            fields_schema[name]["validations"].extend(rules)

        return {**sub_schema, "fields": fields_schema}

    def __validate(self, record: RecordsDataAlias, timezone: ZoneInfo, all_fields: bool):
        for name, rules in self.validations.items():
            if all_fields is True or name in record.keys():
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
                            rule = f"{validator['operator'].value}({value})"
                        else:
                            rule = validator["operator"].value

                        raise ValidationError(f"{message} '{rule}'")
