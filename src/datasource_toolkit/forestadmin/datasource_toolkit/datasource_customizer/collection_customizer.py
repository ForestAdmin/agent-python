from typing import Any, Dict, List, Literal, Optional, Union, cast

from forestadmin.datasource_toolkit.decorators.action.collections import ActionCollectionDecorator
from forestadmin.datasource_toolkit.decorators.action.types.actions import ActionDict
from forestadmin.datasource_toolkit.decorators.binary.collection import BinaryCollectionDecorator
from forestadmin.datasource_toolkit.decorators.chart.chart_collection_decorator import ChartCollectionDecorator
from forestadmin.datasource_toolkit.decorators.chart.types import CollectionChartDefinition
from forestadmin.datasource_toolkit.decorators.computed.collections import ComputedCollectionDecorator
from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.decorators.decorator_stack import DecoratorStack
from forestadmin.datasource_toolkit.decorators.hook.collections import CollectionHookDecorator
from forestadmin.datasource_toolkit.decorators.hook.types import CrudMethod, HookHandler, Position
from forestadmin.datasource_toolkit.decorators.operators_emulate.collections import OperatorsEmulateCollectionDecorator
from forestadmin.datasource_toolkit.decorators.operators_emulate.types import OperatorDefinition
from forestadmin.datasource_toolkit.decorators.override.collection import OverrideCollectionDecorator
from forestadmin.datasource_toolkit.decorators.override.types import (
    CreateOverrideHandler,
    DeleteOverrideHandler,
    UpdateOverrideHandler,
)
from forestadmin.datasource_toolkit.decorators.publication.collections import PublicationCollectionDecorator
from forestadmin.datasource_toolkit.decorators.relation.collections import RelationCollectionDecorator
from forestadmin.datasource_toolkit.decorators.relation.types import (
    PartialManyToMany,
    PartialManyToOne,
    PartialOneToMany,
    PartialOneToOne,
    RelationDefinition,
)
from forestadmin.datasource_toolkit.decorators.rename_field.collections import RenameFieldCollectionDecorator
from forestadmin.datasource_toolkit.decorators.schema.collection import SchemaCollectionDecorator
from forestadmin.datasource_toolkit.decorators.search.collections import SearchCollectionDecorator, SearchDefinition
from forestadmin.datasource_toolkit.decorators.segments.collections import SegmentAlias, SegmentCollectionDecorator
from forestadmin.datasource_toolkit.decorators.sort_emulate.collections import SortCollectionDecorator
from forestadmin.datasource_toolkit.decorators.validation.collection import ValidationCollectionDecorator
from forestadmin.datasource_toolkit.decorators.write.write_replace.types import WriteDefinition
from forestadmin.datasource_toolkit.decorators.write.write_replace.write_replace_collection import (
    WriteReplaceCollection,
)
from forestadmin.datasource_toolkit.interfaces.fields import (
    LITERAL_OPERATORS,
    Column,
    FieldType,
    Operator,
    PrimitiveType,
)
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema
from forestadmin.datasource_toolkit.interfaces.query.sort import PlainSortClause
from forestadmin.datasource_toolkit.plugins.add_external_relation import AddExternalRelation, ExternalRelationDefinition
from forestadmin.datasource_toolkit.plugins.import_field import ImportField, ImportFieldOption
from forestadmin.datasource_toolkit.utils.collections import CollectionUtils, CollectionUtilsException
from forestadmin.datasource_toolkit.validations.rules import MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE
from typing_extensions import Self


class CollectionCustomizer:
    def __init__(
        self,
        datasource_customizer: "DatasourceCustomizer",  # noqa: F821 # type: ignore
        stack: DecoratorStack,
        collection_name: str,
    ):
        self.datasource_customizer = datasource_customizer
        self.stack = stack
        self.collection_name = collection_name

    @property
    def schema(self) -> CollectionSchema:
        return self.stack.validation.get_collection(self.collection_name).schema

    # override CUD
    def override_create(self, handler: CreateOverrideHandler) -> Self:
        """Override the default create behavior of datasource for this collection

        Args:
            handler (CreateOverrideHandler): the new create method

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/hooks/collection-override

        Example:
            def create(context: CreateOverrideCustomizationContext):
                req = requests.post("https://external_api/my_collection", json=context.data)
                return req.json()

            .override_create(create)
        """

        async def _override_create():
            cast(
                OverrideCollectionDecorator, self.stack.override.get_collection(self.collection_name)
            ).add_create_handler(handler)

        self.stack.queue_customization(_override_create)
        return self

    def override_update(self, handler: UpdateOverrideHandler) -> Self:
        """Override the default update behavior of datasource for this collection

        Args:
            handler (UpdateOverrideHandler): the new update method

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/hooks/collection-override

        Example:
            def update(context: UpdateOverrideCustomizationContext):
                pk = context.patch['id']
                req = requests.put(f"https://external_api/my_collection/{pk}", json=context.data)

            .override_update(update)
        """

        async def _override_update():
            cast(
                OverrideCollectionDecorator, self.stack.override.get_collection(self.collection_name)
            ).add_update_handler(handler)

        self.stack.queue_customization(_override_update)
        return self

    def override_delete(self, handler: DeleteOverrideHandler) -> Self:
        """Override the default delete behavior of datasource for this collection

        Args:
            handler (DeleteOverrideCustomizationContext): the new delete method

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/hooks/collection-override

        Example:
            def update(context: UpdateOverrideCustomizationContext):
                pk = context.filter.value
                req = requests.delete(f"https://external_api/my_collection/{pk}")

            .override_update(update)
        """

        async def _override_delete():
            cast(
                OverrideCollectionDecorator, self.stack.override.get_collection(self.collection_name)
            ).add_delete_handler(handler)

        self.stack.queue_customization(_override_delete)
        return self

    # action

    def add_action(self, name: str, action: ActionDict) -> Self:
        """Add a new action on the collection.

        Args:
            name (str): the name of the action
            action (ActionAlias): The definition of the action

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/actions

        Example:
            async def execute(
                context: ActionContextBulk, result_builder: ResultBuilder
            ) -> Union[None, ActionResult]:
                ...perform work here

            .add_action("Mark as live",{
                "scope": ActionsScope.SINGLE,
                "execute": execute,  # this method can be a callable, awaitable or a lambda
            })
        """

        async def _add_action():
            cast(ActionCollectionDecorator, self.stack.action.get_collection(self.collection_name)).add_action(
                name, action
            )

        self.stack.queue_customization(_add_action)
        return self

    # segment

    def add_segment(self, name: str, segment: SegmentAlias) -> Self:
        """Add a new segment on the collection.

        Args:
            name (str): the name of the segment
            segment (SegmentAlias): a function used to generate a condition tree

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/segments

        Example:
            def more_than_two_books_segment(context: CollectionCustomizationContext):
                return ConditionTreeLeaf(
                    field="book_count",
                    operator=Operator.GREATER_THAN,
                    value=2,
                )

            .add_segment("Wrote more than 2 books", pending_order_segment)
        """

        async def _add_segment():
            cast(SegmentCollectionDecorator, self.stack.segment.get_collection(self.collection_name)).add_segment(
                name, segment
            )

        self.stack.queue_customization(_add_segment)
        return self

    # fields

    # # add rename remove
    def add_field(self, name: str, computed_definition: ComputedDefinition) -> Self:
        """Add a new field on the collection.

        Args:
            name (str): The name of the field
            computed_definition (ComputedDefinition): The definition of the field

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/fields/computed

        Example:
            def get_full_name(records: List[RecordsDataAlias], context: CollectionCustomizationContext):
                return [f"{record['first_name']} - {record['last_name']}" for record in records]

            .add_field(
                "full_name",
                {
                    "column_type": PrimitiveType.STRING,
                    "dependencies": ["firs_nName", "last_name"],
                    "get_values": lambda records, context: [
                        f"{record['first_name']} - {record['last_name']}"
                        for record in records
                    ],
                },

            )
        """

        async def _add_field():
            collection_before_relations = self.stack.early_computed.get_collection(self.collection_name)
            collection_after_relations = self.stack.late_computed.get_collection(self.collection_name)
            can_be_compted_before_relations = True
            for dependency in computed_definition["dependencies"]:
                try:
                    CollectionUtils.get_field_schema(collection_before_relations, dependency)
                except CollectionUtilsException:
                    can_be_compted_before_relations = False
                    break

            collection = cast(
                ComputedCollectionDecorator,
                collection_before_relations if can_be_compted_before_relations else collection_after_relations,
            )
            collection.register_computed(name, computed_definition)

        self.stack.queue_customization(_add_field)
        return self

    def import_field(self, name: str, options: ImportFieldOption) -> Self:
        """Import a field from a many to one or one to one relation.

        Args:
            name (str): the name of the field that will be created on the collection
            options (ImportFieldOption): options to import the field

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/fields/import-rename-delete#moving-fields

        Example:
            .import_field('authorName', {"path": "author:fullName"})
        """
        self.use(ImportField, {"name": name, **options})
        return self

    def rename_field(self, current_name: str, new_name: str) -> Self:
        """Allow to rename a field of a given collection.

        Args:
            current_name (str): The current name of the field in a given collection
            new_name (str): The new name of the field

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-nodejs/agent-customization/fields/import-rename-delete

        Example:
            .rename_field("current_name", "new_name")
        """

        async def _rename_field():
            cast(
                RenameFieldCollectionDecorator, self.stack.rename_field.get_collection(self.collection_name)
            ).rename_field(current_name, new_name)

        self.stack.queue_customization(_rename_field)
        return self

    def remove_field(self, *fields) -> Self:
        """Remove fields from the exported schema (they will still be usable within the agent).

        Args:
            fields (list(str)): The name of the fields to remove

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/pagination

        Example:
            .remove_field("field_to_remove", "another_field_to_remove")
        """

        async def _remove_field():
            stack_collection = cast(
                PublicationCollectionDecorator, self.stack.publication.get_collection(self.collection_name)
            )
            for field in fields:
                stack_collection.change_field_visibility(field, False)

        self.stack.queue_customization(_remove_field)
        return self

    # # validation
    def add_field_validation(self, name: str, operator: Union[Operator, LITERAL_OPERATORS], value: Any) -> Self:
        """Add a new validator to the edition form of a given field

        Args:
            name (str): The name of the field
            operator (Operator): The validator  that you wish to add
            value (Any): A configuration value that the validator may need

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/fields/validation

        Example:
            .add_field_validation("first_name", Operator.LONGER_THAN, 2)
        """

        async def _add_field_validation():
            cast(
                ValidationCollectionDecorator, self.stack.validation.get_collection(self.collection_name)
            ).add_validation(name, {"operator": Operator(operator), "value": value})

        self.stack.queue_customization(_add_field_validation)
        return self

    # # operators
    def replace_field_operator(
        self, name: str, operator: Union[Operator, LITERAL_OPERATORS], replacer: OperatorDefinition
    ) -> Self:
        """Replace an implementation for a specific operator on a specific field.
            The operator replacement will be done by the datasource.

        Args:
            name (str): the name of the field to filter on
            operator (Operator): the operator to replace
            replacer (OperatorDefinition): the proposed implementation

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/fields/filter#substitution

        Example:
            .replace_field_operator("fullName", Operator.CONTAINS, lambda value, context: ConditionTreeBranch('or', [
                    ConditionTreeLeaf("firstName", Operator.CONTAINS, value),
                    ConditionTreeLeaf("lastName", Operator.CONTAINS, value),
                ]
            ))
        """

        async def _replace_field_operator():
            if self.stack.early_op_emulate.get_collection(self.collection_name).schema["fields"].get(name) is not None:
                collection = self.stack.early_op_emulate.get_collection(self.collection_name)
            else:
                collection = self.stack.late_op_emulate.get_collection(self.collection_name)
            cast(OperatorsEmulateCollectionDecorator, collection).replace_field_operator(
                name, Operator(operator), replacer
            )

        self.stack.queue_customization(_replace_field_operator)
        return self

    def emulate_field_operator(self, name: str, operator: Union[Operator, LITERAL_OPERATORS]) -> Self:
        """Enable filtering on a specific field with a specific operator using emulation.
            As for all the emulation method, the field filtering will be done in-memory.

        Args:
            name (str): the name of the field to enable emulation on
            operator (Operator): the operator to emulate

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/fields/filter

        Example:
            .emulate_field_operator("fullName", Operator.CONTAINS)
        """

        async def _emulate_field_operator():
            if self.stack.early_op_emulate.get_collection(self.collection_name).schema["fields"].get(name) is not None:
                collection = self.stack.early_op_emulate.get_collection(self.collection_name)
            else:
                collection = self.stack.late_op_emulate.get_collection(self.collection_name)
            cast(OperatorsEmulateCollectionDecorator, collection).emulate_field_operator(name, Operator(operator))

        self.stack.queue_customization(_emulate_field_operator)
        return self

    # # writing
    def replace_field_writing(self, name: str, definition: WriteDefinition) -> Self:
        """Replace the write behavior of a field.

        Args:
            name (str): the name of the field
            definition (WriteDefinition): the function or a value to represent the write behavior

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/fields/write

        Example:
            .replace_field_writing("fullName", lambda value, context: {
                "firstName": value.split(' ')[0], "lastName": value.split(' ', 1)[1]
            })
        """

        async def _replace_field_writing():
            cast(WriteReplaceCollection, self.stack.write.get_collection(self.collection_name)).replace_field_writing(
                name, definition
            )

        self.stack.queue_customization(_replace_field_writing)
        return self

    # # filtering
    def emulate_field_filtering(self, name: str) -> Self:
        """Enable filtering on a specific field using emulation.
            As for all the emulation method, the field filtering will be done in-memory.

        Args:
            name (str): the name of the field to enable emulation on

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/fields/filter#emulation

        Example:
            .emulate_field_filtering("fullName")
        """

        async def _emulate_field_filtering():
            collection = self.stack.late_op_emulate.get_collection(self.collection_name)
            field = collection.schema["fields"][name]

            field_type = cast(Column, field)["column_type"]
            if isinstance(field_type, PrimitiveType):
                operators = MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE[field_type]
                for operator in operators:
                    if operator not in cast(set, field.get("filter_operators", set())):
                        self.emulate_field_operator(name, operator)

        self.stack.queue_customization(_emulate_field_filtering)
        return self

    # # sorting
    def emulate_field_sorting(self, name: str) -> Self:
        """Enable sorting on a specific field using emulation.
            As for all the emulation method, the field sorting will be done in-memory.

        Args:
            name (str): the name of the field to enable emulation on

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/fields/sort#emulation

        Example:
            .emulate_field_sorting('fullName')
        """

        async def _emulate_field_sorting():
            cast(
                SortCollectionDecorator, self.stack.sort_emulate.get_collection(self.collection_name)
            ).emulate_field_sorting(name)

        self.stack.queue_customization(_emulate_field_sorting)
        return self

    def replace_field_sorting(self, name: str, equivalent_sort: List[PlainSortClause]) -> Self:
        """Replace an implementation for the sorting.
            The field sorting will be done by the datasource.

        Args:
            name (str): the name of the field to enable sort
            equivalent_sort (List[PlainSortClause]): the sort equivalent

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/fields/sort

        Example:
            .replace_field_sorting('fullName', [
                {"field": "firstName", "ascending": True},
                {"field": "lastName", "ascending": True},
            ])
        """

        async def _replace_field_sorting():
            cast(
                SortCollectionDecorator, self.stack.sort_emulate.get_collection(self.collection_name)
            ).replace_field_sorting(name, equivalent_sort)

        self.stack.queue_customization(_replace_field_sorting)
        return self

    # # binary
    def replace_field_binary_mode(self, name: str, binary_mode: Union[Literal["datauri"], Literal["hex"]]) -> Self:
        """Choose how binary data should be transported to the GUI.
            By default, all fields are transported as 'datauri', with the exception of primary and foreign keys.

        Args:
            name (str): the name of the field
            binary_mode (str): binary mode to use (either 'datauri' or 'hex')

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/fields/binary

        Example:
            .replace_field_binary_mode('avatar', 'datauri')
        """

        async def _replace_field_binary_mode():
            cast(BinaryCollectionDecorator, self.stack.binary.get_collection(self.collection_name)).set_binary_mode(
                name, binary_mode
            )

        self.stack.queue_customization(_replace_field_binary_mode)
        return self

    # collection

    def disable_count(self) -> Self:
        """Disable count in list view pagination for improved performance.

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/pagination

        Example:
            .disable_count()
        """

        async def _disable_count():
            cast(SchemaCollectionDecorator, self.stack.schema.get_collection(self.collection_name)).override_schema(
                "countable", False
            )

        self.stack.queue_customization(_disable_count)
        return self

    def replace_search(self, definition: SearchDefinition) -> Self:
        """Replace the behavior of the search bar
        Args:
            definition (SearchDefinition): handler to describe the new behavior

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/search

        Example:
            .replace_search(lambda search_string, extended_mode, context: ConditionTreeLeaf(
                    "name", Operator.CONTAINS, search_string
                )
            )
        """

        async def _replace_search():
            cast(SearchCollectionDecorator, self.stack.search.get_collection(self.collection_name)).replace_search(
                definition
            )

        self.stack.queue_customization(_replace_search)
        return self

    def add_chart(self, name: str, definition: CollectionChartDefinition) -> Self:
        """Create a new API chart

        Args:
            name (str): name of the chart
            definition (CollectionChartDefinition): definition of the chart

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/charts

        Example:
            .add_chart("numCustomers", lambda context, result_builder: result_builder.distribution(
                {"tomatoes": 10, "potatoes":20, "carrots": 30}
            ))
        """

        async def _add_chart():
            cast(ChartCollectionDecorator, self.stack.chart.get_collection(self.collection_name)).add_chart(
                name, definition
            )

        self.stack.queue_customization(_add_chart)
        return self

    # relations

    def add_many_to_one_relation(
        self, name: str, foreign_collection: str, foreign_key: str, foreign_key_target: Optional[str] = None
    ) -> Self:
        """Add a many to one relation to the collection

        Args:
            name (str): name of the new relation
            foreign_collection (str): name of the targeted collection
            foreign_key (str): name of the foreign key
            foreign_key_target (str, optional): the target name of the foreign key
                Defaults to the foreign collection primary key

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/relationships/single-record#many-to-one-relations

        Example:
            .add_many_to_one_relation('myAuthor', 'persons', 'authorId')
        """
        self._add_relation(
            name,
            PartialManyToOne(
                type=FieldType.MANY_TO_ONE,
                foreign_collection=foreign_collection,
                foreign_key=foreign_key,
                foreign_key_target=foreign_key_target,
            ),
        )
        return self

    def add_one_to_many_relation(
        self, name: str, foreign_collection: str, origin_key: str, origin_key_target: Optional[str] = None
    ) -> Self:
        """Add a one to many relation to the collection

        Args:
            name (str): name of the new relation
            foreign_collection (str): name of the targeted collection
            origin_key (str): name of the origin key
            origin_key_target (str, optional): the target name of the origin key
                Defaults to the origin collection primary key

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/relationships/multiple-records#one-to-many-relations

        Example:
            .add_one_to_many_relation('writtenBooks', 'books', 'authorId')
        """
        self._add_relation(
            name,
            PartialOneToMany(
                type=FieldType.ONE_TO_MANY,
                foreign_collection=foreign_collection,
                origin_key=origin_key,
                origin_key_target=origin_key_target,
            ),
        )
        return self

    def add_one_to_one_relation(
        self, name: str, foreign_collection: str, origin_key: str, origin_key_target: Optional[str] = None
    ) -> Self:
        """Add a one to one relation to the collection

        Args:
            name (str): name of the new relation
            foreign_collection (str): name of the targeted collection
            origin_key (str): name of the origin key
            origin_key_target (str, optional): the target name of the origin key
                Defaults to the origin collection primary key

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/relationships/single-record#one-to-one-relations

        Example:
            .add_one_to_one_relation('bestFriend', 'persons', 'bestFriendId')
        """
        self._add_relation(
            name,
            PartialOneToOne(
                type=FieldType.ONE_TO_ONE,
                foreign_collection=foreign_collection,
                origin_key=origin_key,
                origin_key_target=origin_key_target,
            ),
        )
        return self

    def add_many_to_many_relation(
        self,
        name: str,
        foreign_collection: str,
        through_collection: str,
        origin_key: str,
        foreign_key: str,
        origin_key_target: Optional[str] = None,
        foreign_key_target: Optional[str] = None,
    ) -> Self:
        """Add a many to many relation to the collection

        Args:
            name (str): name of the new relation
            foreign_collection (str): name of the targeted collection
            through_collection (str): name of the intermediary collection
            origin_key (str): name of the origin key
            foreign_key (str): name of the foreign key
            origin_key_target (Optional[str], optional): the target name of the foreign key
                Defaults to the foreign collection primary key
            foreign_key_target (Optional[str], optional): the target name of the origin key
                Defaults to the origin collection primary key

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/relationships/multiple-records#many-to-many-relations

        Example:
            .add_many_to_many_relation('rentalsOfThisDvd', 'rentals', 'dvdRentals', 'dvdId', 'rentalId')
        """

        self._add_relation(
            name,
            PartialManyToMany(
                through_collection=through_collection,
                foreign_collection=foreign_collection,
                foreign_key=foreign_key,
                foreign_key_target=foreign_key_target,
                origin_key=origin_key,
                origin_key_target=origin_key_target,
                type=FieldType.MANY_TO_MANY,
            ),
        )
        return self

    def _add_relation(self, name: str, definition: RelationDefinition) -> Self:
        async def __add_relation():
            cast(RelationCollectionDecorator, self.stack.relation.get_collection(self.collection_name)).add_relation(
                name, definition
            )

        self.stack.queue_customization(__add_relation)
        return self

    def add_external_relation(self, name: str, definition: ExternalRelationDefinition) -> Self:
        """Add a virtual collection into the related data of a record.

        Args:
            name (str): name of the relation
            definition (AddExternalRelationOptions): the definition of the new relation

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/relationships/multiple-records#external-relations

        Example:
            .add_external_relation("states",
            {
                "schema": {"code": PrimitiveType.Number, "name": PrimitiveType.STRING},
                "list_records": lambda record, context: [
                    {"code": "AL", "name": "Alabama"},
                    {"code": "AK", "name": "Alaska"},
                ]
                if record["id"] == 34
                else [{"code": "AZ", "name": "Arizona"}, {"code": "TX", "name": "Texas"}],
            },
        )
        """
        self.use(AddExternalRelation, {"name": name, **definition})
        return self

    # hook

    def add_hook(self, position: Position, type: CrudMethod, handler: HookHandler) -> Self:
        """Add a new hook handler to an action

        Args:
            position (Position): Either if the hook is executed before or after the action ({"Before", "After"})
            type (CrudMethod): Type of action which should be hooked
                ({"List", "Create", "Update", "Delete", "Aggregate"})
            handler (HookHandler): Callback that should be executed when the hook is triggered

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/hooks

        Example:
            .add_hook('Before', 'List', lambda context: # do something before list action )
        """

        async def _add_hook():
            cast(CollectionHookDecorator, self.stack.hook.get_collection(self.collection_name)).add_hook(
                position, type, handler
            )

        self.stack.queue_customization(_add_hook)
        return self

    # plugin

    def use(self, plugin: type, options: Optional[Dict] = {}) -> Self:
        """Load a plugin on the collection.

        Args:
            plugin (type): plugin class
            options (Dict, optional): options to pass to the plugin

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/plugins

        Example:
            .use(CreateFileField, { "fieldname": 'avatar' })
        """

        async def _use():
            await plugin().run(self.datasource_customizer, self, options)

        self.stack.queue_customization(_use)
        return self
