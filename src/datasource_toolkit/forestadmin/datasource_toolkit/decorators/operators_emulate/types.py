from typing import Any, Awaitable, Callable, Union

from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree

OperatorDefinition = Callable[[Any, CollectionCustomizationContext], Union[ConditionTree, Awaitable[ConditionTree]]]
