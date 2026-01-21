from typing import Dict

from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation, Aggregator, DateOperation


class AggregatorSerializer:
    @staticmethod
    def serialize(aggregator: Aggregator) -> str:
        if isinstance(aggregator, Aggregator):
            return aggregator.value
        return aggregator

    @staticmethod
    def deserialize(aggregator: str) -> Aggregator:
        return Aggregator(aggregator)


class DateOperationSerializer:
    @staticmethod
    def serialize(date_operation: DateOperation) -> str:
        return date_operation.value

    @staticmethod
    def deserialize(date_operation: str) -> DateOperation:
        return DateOperation(date_operation)


class AggregationSerializer:
    @staticmethod
    def serialize(aggregation: Aggregation) -> Dict:
        return {
            "field": aggregation.field,
            "operation": AggregatorSerializer.serialize(aggregation.operation),
            "groups": [
                {
                    "field": group["field"],
                    "operation": (
                        DateOperationSerializer.serialize(group["operation"]) if "operation" in group else None
                    ),
                }
                for group in aggregation.groups
            ],
        }

    @staticmethod
    def deserialize(aggregation: Dict) -> Aggregation:
        groups = []
        for group in aggregation["groups"]:
            tmp = {
                "field": group["field"],
            }
            if group["operation"] is not None:
                tmp["operation"] = DateOperationSerializer.deserialize(group["operation"])

            groups.append(tmp)

        return Aggregation(
            {
                "field": aggregation["field"],
                "operation": AggregatorSerializer.deserialize(aggregation["operation"]),
                "groups": groups,
            }
        )
