import asyncio
import sys
from unittest import TestCase
from unittest.mock import AsyncMock, patch

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.decorators.relation.collections import RelationCollectionDecorator
from forestadmin.datasource_toolkit.decorators.relation.types import (
    PartialManyToMany,
    PartialManyToOne,
    PartialOneToMany,
    PartialOneToOne,
)
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException, ForestException
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, ManyToOne, Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.query.sort import PlainSortClause, Sort


class BaseRelationDecoratorTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()

        Collection.__abstractmethods__ = set()  # to instantiate abstract class

        # passport collection
        cls.collection_pictures = Collection("Pictures", cls.datasource)
        cls.collection_pictures.add_fields(
            {
                "picture_id": Column(
                    type=FieldType.COLUMN,
                    column_type=PrimitiveType.NUMBER,
                    is_primary_key=True,
                    filter_operators=set([Operator.IN]),
                ),
                "filename": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
                "other_id": Column(column_type=PrimitiveType.NUMBER, type=FieldType.COLUMN),
            }
        )

        cls.collection_passports = Collection("Passports", cls.datasource)
        cls.collection_passports.add_fields(
            {
                "passport_id": Column(
                    type=FieldType.COLUMN,
                    column_type=PrimitiveType.NUMBER,
                    is_primary_key=True,
                    filter_operators=set([Operator.IN]),
                ),
                "issue_date": Column(column_type=PrimitiveType.DATE_ONLY, type=FieldType.COLUMN),
                "owner_id": Column(
                    column_type=PrimitiveType.NUMBER, filter_operators=set([Operator.IN]), type=FieldType.COLUMN
                ),
                "picture_id": Column(column_type=PrimitiveType.NUMBER, type=FieldType.COLUMN),
                "picture": ManyToOne(
                    type=FieldType.MANY_TO_ONE, foreign_collection="Pictures", foreign_key="picture_id"
                ),
            }
        )
        cls.passport_records = [
            {
                "passport_id": 101,
                "issue_date": "2010-01-01",
                "owner_id": 202,
                "picture_id": 301,
                "picture": {"picture_id": 301, "filename": "pic1.jpg"},
            },
            {
                "passport_id": 102,
                "issue_date": "2017-01-01",
                "owner_id": 201,
                "picture_id": 302,
                "picture": {"picture_id": 302, "filename": "pic2.jpg"},
            },
            {
                "passport_id": 103,
                "issue_date": "2017-02-05",
                "owner_id": None,
                "picture_id": 303,
                "picture": {"picture_id": 303, "filename": "pic3.jpg"},
            },
        ]

        async def mocked_passport_list(caller: User, filter_: PaginatedFilter, projection: Projection):
            result = [*cls.passport_records]
            if filter_ and filter_.condition_tree:
                result = filter_.condition_tree.filter(result, cls.collection_passports, caller.timezone)
            if filter_ and filter_.sort:
                result = filter_.sort.apply(result)
            return projection.apply(result)

        async def mocked_passport_aggregate(caller: User, filter_: Filter, aggregate: Aggregation, limit):
            return aggregate.apply(cls.passport_records, caller.timezone)

        cls.collection_passports.list = AsyncMock(side_effect=mocked_passport_list)
        cls.collection_passports.aggregate = AsyncMock(side_effect=mocked_passport_aggregate)

        # collection person
        cls.collection_person = Collection("Persons", cls.datasource)
        cls.collection_person.add_fields(
            {
                "person_id": Column(
                    type=FieldType.COLUMN,
                    column_type=PrimitiveType.NUMBER,
                    is_primary_key=True,
                    filter_operators=set([Operator.IN]),
                ),
                "other_id": Column(
                    column_type=PrimitiveType.NUMBER, filter_operators=set([Operator.IN]), type=FieldType.COLUMN
                ),
                "name": Column(
                    column_type=PrimitiveType.STRING, filter_operators=set([Operator.IN]), type=FieldType.COLUMN
                ),
            }
        )
        cls.persons_records = [
            {"person_id": 201, "other_id": 201, "name": "Sharon J. Whalen"},
            {"person_id": 202, "other_id": 202, "name": "Mae S. Waldron"},
            {"person_id": 203, "other_id": 203, "name": "Joseph P. Rodriguez"},
        ]

        async def mocked_person_list(caller: User, filter_: PaginatedFilter, projection: Projection):
            result = [*cls.persons_records]
            if filter_ and filter_.condition_tree:
                result = filter_.condition_tree.filter(result, cls.collection_person, caller.timezone)
            if filter_ and filter_.sort:
                result = filter_.sort.apply(result)
            return projection.apply(result)

        async def mocked_person_aggregate(caller: User, filter_: Filter, aggregate: Aggregation, limit):
            return aggregate.apply(cls.persons_records, caller.timezone)

        cls.collection_person.list = AsyncMock(side_effect=mocked_person_list)
        cls.collection_person.aggregate = AsyncMock(side_effect=mocked_person_aggregate)

        cls.datasource.add_collection(cls.collection_pictures)
        cls.datasource.add_collection(cls.collection_passports)
        cls.datasource.add_collection(cls.collection_person)

        cls.mocked_caller = User(
            rendering_id=1,
            user_id=1,
            tags={},
            email="dummy@user.fr",
            first_name="dummy",
            last_name="user",
            team="operational",
            timezone=zoneinfo.ZoneInfo("Europe/Paris"),
        )

    def setUp(self) -> None:
        self.decorated_datasource = DatasourceDecorator(self.datasource, RelationCollectionDecorator)
        self.decorated_passports = self.decorated_datasource.get_collection("Passports")
        self.decorated_persons = self.decorated_datasource.get_collection("Persons")


class TestOneToOneRelationCreation(BaseRelationDecoratorTest):
    def test_missing_dependency_should_fail(self):
        self.assertRaisesRegex(
            DatasourceToolkitException,
            r"🌳🌳🌳Column not found: Passports.__non_existing__."
            + r" Fields in Passports are passport_id, issue_date, owner_id, picture_id, picture",
            self.decorated_persons.add_relation,
            "persons",
            PartialOneToOne(type=FieldType.ONE_TO_ONE, foreign_collection="Passports", origin_key="__non_existing__"),
        )

    def test_should_throw_when_IN_not_supported_by_fk_in_target(self):
        with patch.dict(self.collection_passports.schema["fields"]["owner_id"], {"filter_operators": set()}):
            self.assertRaisesRegex(
                ForestException,
                r"🌳🌳🌳Column does not support the In operator: 'Passports.owner_id'",
                self.decorated_persons.add_relation,
                "passports",
                PartialOneToOne(type=FieldType.ONE_TO_ONE, foreign_collection="Passports", origin_key="owner_id"),
            )

    def test_origin_key_target_and_target_not_same_type(self):
        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳Types from 'Passports.owner_id' and 'Persons.name' do not match.",
            self.decorated_persons.add_relation,
            "passport",
            PartialOneToOne(
                type=FieldType.ONE_TO_ONE,
                foreign_collection="Passports",
                origin_key="owner_id",
                origin_key_target="name",
            ),
        )

    def test_should_work_with_correct_origin_key_target(self):
        self.decorated_persons.add_relation(
            "passport",
            PartialOneToOne(
                type=FieldType.ONE_TO_ONE,
                foreign_collection="Passports",
                origin_key="owner_id",
                origin_key_target="person_id",
            ),
        )
        self.assertEqual(self.decorated_persons.schema["fields"]["passport"]["type"], FieldType.ONE_TO_ONE)

    def test_should_work_without_origin_key_target(self):
        self.decorated_persons.add_relation(
            "passport",
            PartialOneToOne(
                type=FieldType.ONE_TO_ONE,
                foreign_collection="Passports",
                origin_key="owner_id",
            ),
        )
        self.assertEqual(self.decorated_persons.schema["fields"]["passport"]["type"], FieldType.ONE_TO_ONE)


class TestOneToManyRelationCreation(BaseRelationDecoratorTest):
    def test_origin_key_target_and_target_not_same_type(self):
        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳Types from 'Passports.owner_id' and 'Persons.name' do not match.",
            self.decorated_persons.add_relation,
            "passports",
            PartialOneToMany(
                type=FieldType.ONE_TO_MANY,
                foreign_collection="Passports",
                origin_key="owner_id",
                origin_key_target="name",
            ),
        )

    def test_should_work_with_correct_origin_key_target(self):
        self.decorated_persons.add_relation(
            "passport",
            PartialOneToMany(
                type=FieldType.ONE_TO_MANY,
                foreign_collection="Passports",
                origin_key="owner_id",
                origin_key_target="person_id",
            ),
        )
        self.assertEqual(self.decorated_persons.schema["fields"]["passport"]["type"], FieldType.ONE_TO_MANY)

    def test_should_work_without_origin_key_target(self):
        self.decorated_persons.add_relation(
            "passport",
            PartialOneToMany(
                type=FieldType.ONE_TO_MANY,
                foreign_collection="Passports",
                origin_key="owner_id",
            ),
        )
        self.assertEqual(self.decorated_persons.schema["fields"]["passport"]["type"], FieldType.ONE_TO_MANY)


class TestManyToOneRelationCreation(BaseRelationDecoratorTest):
    def test_should_raise_on_non_existent_collection(self):
        self.assertRaisesRegex(
            DatasourceToolkitException,
            r"🌳🌳🌳Collection '__non_exits__' not found. Available collections are: Pictures, Passports, Persons",
            self.decorated_passports.add_relation,
            "some_name",
            PartialManyToOne(type=FieldType.MANY_TO_ONE, foreign_collection="__non_exits__", foreign_key="owner_id"),
        )

    def test_should_raise_on_non_existent_fk(self):
        self.assertRaisesRegex(
            DatasourceToolkitException,
            r"🌳🌳🌳Column not found: Passports.__non_existent__. "
            + r"Fields in Passports are passport_id, issue_date, owner_id, picture_id, picture",
            self.decorated_passports.add_relation,
            "owner",
            PartialManyToOne(type=FieldType.MANY_TO_ONE, foreign_collection="Persons", foreign_key="__non_existent__"),
        )

    def test_should_throw_when_IN_not_supported_by_pk_in_target(self):
        with patch.dict(self.collection_person.schema["fields"]["person_id"], {"filter_operators": set()}):
            self.assertRaisesRegex(
                ForestException,
                r"🌳🌳🌳Column does not support the In operator: 'Persons.person_id'",
                self.decorated_passports.add_relation,
                "owner",
                PartialManyToOne(type=FieldType.MANY_TO_ONE, foreign_collection="Persons", foreign_key="owner_id"),
            )

    def test_should_work_with_correct_foreign_key_target(self):
        self.decorated_passports.add_relation(
            "owner",
            PartialManyToOne(
                type=FieldType.MANY_TO_ONE,
                foreign_collection="Persons",
                foreign_key="owner_id",
                foreign_key_target="person_id",
            ),
        )
        self.assertEqual(self.decorated_passports.schema["fields"]["owner"]["type"], FieldType.MANY_TO_ONE)

    def test_should_work_without_foreign_key_target(self):
        self.decorated_passports.add_relation(
            "owner",
            PartialManyToOne(
                type=FieldType.MANY_TO_ONE,
                foreign_collection="Persons",
                foreign_key="owner_id",
            ),
        )
        self.assertEqual(self.decorated_passports.schema["fields"]["owner"]["type"], FieldType.MANY_TO_ONE)


class TestManyToManyRelationCreation(BaseRelationDecoratorTest):
    def test_should_raise_on_non_existent_through_collection(self):
        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳Collection '__non_exists__' not found. Available collections are: Pictures, Passports, Persons",
            self.decorated_persons.add_relation,
            "passports",
            PartialManyToMany(
                type=FieldType.MANY_TO_MANY,
                foreign_collection="Passports",
                foreign_key="owner_id",
                origin_key="owner_id",
                through_collection="__non_exists__",
            ),
        )

    def test_should_raise_on_non_existent_origin_key(self):
        self.assertRaisesRegex(
            DatasourceToolkitException,
            r"🌳🌳🌳Column not found: Passports.__non_exists__. Fields in Passports are passport_id, "
            + r"issue_date, owner_id, picture_id, picture",
            self.decorated_persons.add_relation,
            "passports",
            PartialManyToMany(
                type=FieldType.MANY_TO_MANY,
                foreign_collection="Passports",
                foreign_key="owner_id",
                origin_key="__non_exists__",
                through_collection="Passports",
            ),
        )

    def test_should_raise_on_non_existent_fk(self):
        self.assertRaisesRegex(
            DatasourceToolkitException,
            r"🌳🌳🌳Column not found: Passports.__non_exists__. "
            + r"Fields in Passports are passport_id, issue_date, owner_id, picture_id, picture",
            self.decorated_persons.add_relation,
            "passports",
            PartialManyToMany(
                type=FieldType.MANY_TO_MANY,
                foreign_collection="Passports",
                foreign_key="__non_exists__",
                origin_key="owner_id",
                through_collection="Passports",
            ),
        )

    def test_should_raise_when_origin_key_type_not_match(self):
        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳Types from 'Passports.owner_id' and 'Persons.name' do not match.",
            self.decorated_persons.add_relation,
            "persons",
            PartialManyToMany(
                type=FieldType.MANY_TO_MANY,
                foreign_collection="Passports",
                foreign_key="owner_id",
                origin_key="owner_id",
                through_collection="Passports",
                origin_key_target="name",
                foreign_key_target="passport_id",
            ),
        )

    def test_should_work_with_origin_key_target_and_foreign_key_target(self):
        self.decorated_persons.add_relation(
            "persons",
            PartialManyToMany(
                type=FieldType.MANY_TO_MANY,
                foreign_collection="Passports",
                foreign_key="owner_id",
                origin_key="owner_id",
                through_collection="Passports",
                origin_key_target="person_id",
                foreign_key_target="passport_id",
            ),
        )
        self.assertEqual(self.decorated_persons.schema["fields"]["persons"]["type"], FieldType.MANY_TO_MANY)

    def test_should_work_without_origin_key_target_and_foreign_key_target(self):
        self.decorated_persons.add_relation(
            "persons",
            PartialManyToMany(
                type=FieldType.MANY_TO_MANY,
                foreign_collection="Passports",
                foreign_key="owner_id",
                origin_key="owner_id",
                through_collection="Passports",
            ),
        )
        self.assertEqual(self.decorated_persons.schema["fields"]["persons"]["type"], FieldType.MANY_TO_MANY)


class TestEmulatedProjection(BaseRelationDecoratorTest):
    def test_should_fetch_fields_from_many_to_one(self):
        self.decorated_passports.add_relation(
            "owner",
            PartialManyToOne(
                type=FieldType.MANY_TO_ONE,
                foreign_collection="Persons",
                foreign_key="owner_id",
            ),
        )

        records = self.loop.run_until_complete(
            self.decorated_passports.list(
                self.mocked_caller, PaginatedFilter({}), Projection("passport_id", "owner:name")
            )
        )
        self.assertEqual(
            records,
            [
                {"passport_id": 101, "owner": {"name": "Mae S. Waldron"}},
                {"passport_id": 102, "owner": {"name": "Sharon J. Whalen"}},
                {"passport_id": 103, "owner": None},
            ],
        )

        self.collection_person.list.assert_awaited_with(
            self.mocked_caller,
            PaginatedFilter({"condition_tree": ConditionTreeLeaf("person_id", Operator.IN, [201, 202])}),
            Projection("name", "person_id"),
        )

    def test_should_fetch_fields_from_one_to_one(self):
        self.decorated_persons.add_relation(
            "passport",
            PartialOneToOne(
                type=FieldType.ONE_TO_ONE,
                foreign_collection="Passports",
                origin_key="owner_id",
                origin_key_target="other_id",
            ),
        )
        records = self.loop.run_until_complete(
            self.decorated_persons.list(
                self.mocked_caller, PaginatedFilter({}), Projection("person_id", "name", "passport:issue_date")
            )
        )
        self.assertEqual(
            records,
            [
                {"person_id": 201, "name": "Sharon J. Whalen", "passport": {"issue_date": "2017-01-01"}},
                {"person_id": 202, "name": "Mae S. Waldron", "passport": {"issue_date": "2010-01-01"}},
                {"person_id": 203, "name": "Joseph P. Rodriguez", "passport": None},
            ],
        )

    def test_should_fetch_fields_from_one_to_many(self):
        self.decorated_persons.add_relation(
            "passport",
            PartialOneToMany(
                type=FieldType.ONE_TO_MANY,
                foreign_collection="Passports",
                origin_key="owner_id",
                origin_key_target="other_id",
            ),
        )
        records = self.loop.run_until_complete(
            self.decorated_persons.list(
                self.mocked_caller, PaginatedFilter({}), Projection("person_id", "name", "passport:issue_date")
            )
        )
        self.assertEqual(
            records,
            [
                {"person_id": 201, "name": "Sharon J. Whalen", "passport": {"issue_date": "2017-01-01"}},
                {"person_id": 202, "name": "Mae S. Waldron", "passport": {"issue_date": "2010-01-01"}},
                {"person_id": 203, "name": "Joseph P. Rodriguez", "passport": None},
            ],
        )

    def test_should_fetch_fields_from_many_to_many(self):
        self.decorated_persons.add_relation(
            "persons",
            PartialManyToMany(
                type=FieldType.MANY_TO_MANY,
                foreign_collection="Persons",
                foreign_key="owner_id",
                origin_key="owner_id",
                through_collection="Passports",
                origin_key_target="other_id",
                foreign_key_target="person_id",
            ),
        )
        records = self.loop.run_until_complete(
            self.decorated_persons.list(
                self.mocked_caller, PaginatedFilter({}), Projection("person_id", "name", "persons:name")
            )
        )
        self.assertEqual(
            records,
            [
                {"person_id": 201, "name": "Sharon J. Whalen", "persons": None},
                {"person_id": 202, "name": "Mae S. Waldron", "persons": None},
                {"person_id": 203, "name": "Joseph P. Rodriguez", "persons": None},
            ],
        )

    def test_should_fetch_fields_from_native_behind_emulate(self):
        self.decorated_persons.add_relation(
            "passport",
            PartialOneToOne(
                type=FieldType.ONE_TO_ONE,
                foreign_collection="Passports",
                origin_key="owner_id",
            ),
        )
        self.decorated_passports.add_relation(
            "owner",
            PartialManyToOne(
                type=FieldType.MANY_TO_ONE,
                foreign_collection="Persons",
                foreign_key="owner_id",
            ),
        )

        with patch.object(self.collection_pictures, "list", new_callable=AsyncMock) as mocked_picture_list:
            records = self.loop.run_until_complete(
                self.decorated_persons.list(
                    self.mocked_caller,
                    PaginatedFilter({}),
                    Projection("person_id", "name", "passport:picture:filename"),
                )
            )
            mocked_picture_list.assert_not_awaited()
        self.assertEqual(
            records,
            [
                {
                    "person_id": 201,
                    "name": "Sharon J. Whalen",
                    "passport": {"picture": {"filename": "pic2.jpg"}},
                },
                {"person_id": 202, "name": "Mae S. Waldron", "passport": {"picture": {"filename": "pic1.jpg"}}},
                {"person_id": 203, "name": "Joseph P. Rodriguez", "passport": None},
            ],
        )

    def test_should_not_break_with_deep_reprojection(self):
        self.decorated_persons.add_relation(
            "passport",
            PartialOneToOne(
                type=FieldType.ONE_TO_ONE,
                foreign_collection="Passports",
                origin_key="owner_id",
            ),
        )
        self.decorated_passports.add_relation(
            "owner",
            PartialManyToOne(
                type=FieldType.MANY_TO_ONE,
                foreign_collection="Persons",
                foreign_key="owner_id",
            ),
        )
        records = self.loop.run_until_complete(
            self.decorated_persons.list(
                self.mocked_caller,
                PaginatedFilter({}),
                Projection("person_id", "name", "passport:owner:passport:issue_date"),
            )
        )
        self.assertEqual(
            records,
            [
                {
                    "person_id": 201,
                    "name": "Sharon J. Whalen",
                    "passport": {"owner": {"passport": {"issue_date": "2017-01-01"}}},
                },
                {
                    "person_id": 202,
                    "name": "Mae S. Waldron",
                    "passport": {"owner": {"passport": {"issue_date": "2010-01-01"}}},
                },
                {"person_id": 203, "name": "Joseph P. Rodriguez", "passport": None},
            ],
        )


class TestWithTwoEmulatedRelations(BaseRelationDecoratorTest):
    def setUp(self) -> None:
        super().setUp()
        self.decorated_persons.add_relation(
            "passport",
            PartialOneToOne(
                type=FieldType.ONE_TO_ONE,
                foreign_collection="Passports",
                origin_key="owner_id",
            ),
        )
        self.decorated_passports.add_relation(
            "owner",
            PartialManyToOne(
                type=FieldType.MANY_TO_ONE,
                foreign_collection="Persons",
                foreign_key="owner_id",
            ),
        )

    def test_emulate_filtering_should_filter_by_many_to_one(self):
        records = self.loop.run_until_complete(
            self.decorated_passports.list(
                self.mocked_caller,
                PaginatedFilter({"condition_tree": ConditionTreeLeaf("owner:name", Operator.EQUAL, "Mae S. Waldron")}),
                Projection("passport_id", "issue_date"),
            )
        )
        self.assertEqual(
            records,
            [{"passport_id": 101, "issue_date": "2010-01-01"}],
        )

    def test_emulate_filtering_should_filter_by_one_to_one(self):
        records = self.loop.run_until_complete(
            self.decorated_persons.list(
                self.mocked_caller,
                PaginatedFilter(
                    {"condition_tree": ConditionTreeLeaf("passport:issue_date", Operator.EQUAL, "2017-01-01")}
                ),
                Projection("person_id", "name"),
            )
        )
        self.assertEqual(
            records,
            [{"person_id": 201, "name": "Sharon J. Whalen"}],
        )

    def test_emulate_filtering_should_filter_by_native_relation_behind_emulated(self):
        with patch.object(self.collection_pictures, "list", new_callable=AsyncMock) as mocked_picture_list:
            records = self.loop.run_until_complete(
                self.decorated_persons.list(
                    self.mocked_caller,
                    PaginatedFilter(
                        {"condition_tree": ConditionTreeLeaf("passport:picture:filename", Operator.EQUAL, "pic1.jpg")}
                    ),
                    Projection("person_id", "name"),
                )
            )
            mocked_picture_list.assert_not_awaited()
        self.assertEqual(
            records,
            [{"person_id": 202, "name": "Mae S. Waldron"}],
        )

    def test_emulate_filtering_should_not_break_with_deep_filters(self):
        records = self.loop.run_until_complete(
            self.decorated_persons.list(
                self.mocked_caller,
                PaginatedFilter(
                    {
                        "condition_tree": ConditionTreeLeaf(
                            "passport:owner:passport:issue_date", Operator.EQUAL, "2017-01-01"
                        )
                    }
                ),
                Projection("person_id", "name"),
            )
        )
        self.assertEqual(
            records,
            [{"person_id": 201, "name": "Sharon J. Whalen"}],
        )

    def test_emulate_sorting_should_replace_sorts_in_emulate_many_to_one_into_by_fk(self):
        # check both sides to make sure we're not getting lucky
        ascending = self.loop.run_until_complete(
            self.decorated_passports.list(
                self.mocked_caller,
                PaginatedFilter({"sort": Sort([PlainSortClause(field="owner:name", ascending=True)])}),
                Projection("passport_id", "owner_id", "owner:name"),
            )
        )
        descending = self.loop.run_until_complete(
            self.decorated_passports.list(
                self.mocked_caller,
                PaginatedFilter({"sort": Sort([PlainSortClause(field="owner:name", ascending=False)])}),
                Projection("passport_id", "owner_id", "owner:name"),
            )
        )
        self.assertEqual(
            ascending,
            [
                {"passport_id": 103, "owner_id": None, "owner": None},
                {"passport_id": 102, "owner_id": 201, "owner": {"name": "Sharon J. Whalen"}},
                {"passport_id": 101, "owner_id": 202, "owner": {"name": "Mae S. Waldron"}},
            ],
        )
        self.assertEqual(
            descending,
            [
                {"passport_id": 101, "owner_id": 202, "owner": {"name": "Mae S. Waldron"}},
                {"passport_id": 102, "owner_id": 201, "owner": {"name": "Sharon J. Whalen"}},
                {"passport_id": 103, "owner_id": None, "owner": None},
            ],
        )

    def test_emulated_aggregation_should_not_emulate_when_not_needed(self):
        filter_ = Filter({})
        aggregate = Aggregation({"operation": "Count", "groups": [{"field": "name"}]})
        groups = self.loop.run_until_complete(
            self.decorated_persons.aggregate(
                self.mocked_caller,
                filter_,
                aggregate,
            )
        )
        self.collection_person.aggregate.assert_awaited_with(self.mocked_caller, filter_, aggregate, None)
        self.assertEqual(
            groups,
            [
                {"value": 1, "group": {"name": "Sharon J. Whalen"}},
                {"value": 1, "group": {"name": "Mae S. Waldron"}},
                {"value": 1, "group": {"name": "Joseph P. Rodriguez"}},
            ],
        )

    def test_emulated_aggregation_should_give_valid_result_otherwise(self):
        filter_ = Filter({})
        aggregate = Aggregation({"operation": "Count", "groups": [{"field": "passport:picture:filename"}]})
        groups = self.loop.run_until_complete(
            self.decorated_persons.aggregate(self.mocked_caller, filter_, aggregate, 2)
        )
        self.assertEqual(
            groups,
            [
                {"value": 1, "group": {"passport:picture:filename": "pic2.jpg"}},
                {"value": 1, "group": {"passport:picture:filename": "pic1.jpg"}},
            ],
        )
