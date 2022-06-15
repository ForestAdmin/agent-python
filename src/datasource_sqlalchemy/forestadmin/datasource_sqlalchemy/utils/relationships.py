from typing import DefaultDict, List

from sqlalchemy import column as SqlAlchemyColumn

Relationships = DefaultDict[int, List[SqlAlchemyColumn]]


def merge_relationships(r1: Relationships, r2: Relationships) -> Relationships:
    for level, nested_relationship in r2.items():
        r1[level].extend(nested_relationship)
        r1[level] = list(set(r1[level]))
    return r1
