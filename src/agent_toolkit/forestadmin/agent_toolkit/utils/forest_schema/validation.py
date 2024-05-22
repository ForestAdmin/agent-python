from typing import Dict, List, Optional

from forestadmin.agent_toolkit.utils.forest_schema.type import ServerValidationType, ValidationType
from forestadmin.datasource_toolkit.interfaces.fields import Operator, Validation


class FrontendValidationUtils:
    OPERATOR_VALIDATION_TYPE: Dict[Operator, ValidationType] = {
        Operator.PRESENT: ValidationType.PRESENT,
        Operator.GREATER_THAN: ValidationType.GREATER_THAN,
        Operator.LESS_THAN: ValidationType.LESS_THAN,
        Operator.LONGER_THAN: ValidationType.LONGER_THAN,
        Operator.SHORTER_THAN: ValidationType.SHORTER_THAN,
        Operator.CONTAINS: ValidationType.CONTAINS,
        Operator.LIKE: ValidationType.LIKE,
    }

    @classmethod
    def convert_validation_list(cls, predicates: Optional[List[Validation]]):
        if not predicates:
            predicates = []

        res: List[ServerValidationType] = []
        for predicate in predicates:
            validation_type = cls.OPERATOR_VALIDATION_TYPE.get(Operator(predicate["operator"]))
            if validation_type:
                tmp: ServerValidationType = {
                    "type": validation_type.value,
                    "value": predicate.get("value"),
                    # "message": None,
                }
                if tmp.get("value") is None:
                    tmp.pop("value", None)
                res.append(tmp)
        return res
