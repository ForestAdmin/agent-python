from typing import DefaultDict, List

from sqlalchemy import column as SqlAlchemyColumn

Relationships = DefaultDict[int, List[SqlAlchemyColumn]]


def merge_relationships(r1: Relationships, r2: Relationships) -> Relationships:
    for level, nested_relationship in r2.items():
        for relationship in nested_relationship:
            alias = relationship[0]
            if not list(filter(lambda r: r[0].name == alias.name, r1[level])):  # type: ignore
                r1[level].append(relationship)
    return r1
