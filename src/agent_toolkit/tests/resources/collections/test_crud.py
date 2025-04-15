import asyncio
import csv
import importlib
import json
import sys
from unittest import TestCase
from unittest.mock import ANY, AsyncMock, Mock, patch
from uuid import UUID

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

import forestadmin.agent_toolkit.resources.collections.crud
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.resources.collections.exceptions import CollectionResourceException
from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection, RequestCollectionException
from forestadmin.agent_toolkit.services.permissions.ip_whitelist_service import IpWhiteListService
from forestadmin.agent_toolkit.services.permissions.permission_service import PermissionService
from forestadmin.agent_toolkit.services.serializers.exceptions import JsonApiSerializerException
from forestadmin.agent_toolkit.services.serializers.json_api_serializer import JsonApiSerializer
from forestadmin.agent_toolkit.utils.context import Request, RequestMethod, User
from forestadmin.agent_toolkit.utils.csv import CsvException
from forestadmin.datasource_toolkit.collections import Collection, CollectionException
from forestadmin.datasource_toolkit.datasource_customizer.datasource_composite import CompositeDatasource
from forestadmin.datasource_toolkit.datasources import Datasource, DatasourceException
from forestadmin.datasource_toolkit.exceptions import ForbiddenError, NativeQueryException, ValidationError
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection

FAKE_USER = User(
    rendering_id=1,
    user_id=1,
    tags={},
    email="dummy@user.fr",
    first_name="dummy",
    last_name="user",
    team="operational",
    timezone=zoneinfo.ZoneInfo("Europe/Paris"),
    request={"ip": "127.0.0.1"},
)


def authenticate_mock(fn):
    async def wrapped2(self, request):
        request.user = FAKE_USER

        return await fn(self, request)

    return wrapped2


def ip_white_list_mock(fn):
    async def wrapped(self, request: Request, *args, **kwargs):
        return await fn(self, request, *args, **kwargs)

    return wrapped


patch("forestadmin.agent_toolkit.resources.collections.decorators.authenticate", authenticate_mock).start()
patch("forestadmin.agent_toolkit.resources.collections.decorators.ip_white_list", ip_white_list_mock).start()
# how to mock decorators, and why they are not testable :
# https://dev.to/stack-labs/how-to-mock-a-decorator-in-python-55jc

importlib.reload(forestadmin.agent_toolkit.resources.collections.crud)
from forestadmin.agent_toolkit.resources.collections.crud import CrudResource  # noqa: E402


class TestCrudResource(TestCase):
    @classmethod
    def _create_collection(
        cls,
        name,
        fields,
    ):
        collection = Mock(Collection)
        collection._datasource = cls.datasource
        collection.datasource = cls.datasource
        collection.list = AsyncMock(return_value=None)
        collection.update = AsyncMock(return_value=None)
        collection.delete = AsyncMock(return_value=None)
        collection._name = name
        collection.name = name
        collection.get_field = lambda x: collection._schema["fields"][x]
        collection._schema = {
            "actions": {},
            "fields": fields,
            "searchable": True,
            "segments": [],
            "countable": True,
        }
        collection.schema = collection._schema
        return collection

    @classmethod
    def _create_collections(cls):
        # order
        cls.collection_order = cls._create_collection(
            "order",
            {
                "id": {
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": True,
                    "type": FieldType.COLUMN,
                    "filter_operators": set([Operator.IN, Operator.EQUAL]),
                },
                "cost": {"column_type": PrimitiveType.NUMBER, "is_primary_key": False, "type": FieldType.COLUMN},
                "important": {"column_type": PrimitiveType.BOOLEAN, "is_primary_key": False, "type": FieldType.COLUMN},
                "products": {
                    "foreign_collection": "product",
                    "origin_key": "order_id",
                    "origin_key_target": "id",
                    "type": FieldType.ONE_TO_MANY,
                },
                "status_id": {
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": False,
                    "type": FieldType.COLUMN,
                    "filter_operators": set([Operator.IN, Operator.EQUAL]),
                },
                "status": {
                    "type": FieldType.MANY_TO_ONE,
                    "foreign_collection": "status",
                    "foreign_key_target": "id",
                    "foreign_key": "status_id",
                },
                "cart": {
                    "type": FieldType.ONE_TO_ONE,
                    "foreign_collection": "cart",
                    "origin_key_target": "id",
                    "origin_key": "order_id",
                },
                "tags": {
                    "type": FieldType.POLYMORPHIC_ONE_TO_ONE,
                    "foreign_collection": "tag",
                    "origin_key": "taggable_id",
                    "origin_key_target": "id",
                    "origin_type_field": "taggable_type",
                    "origin_type_value": "order",
                },
            },
        )

        # status
        cls.collection_status = cls._create_collection(
            "status",
            {
                "id": {
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": True,
                    "type": FieldType.COLUMN,
                    "filter_operators": set([Operator.IN, Operator.EQUAL]),
                },
                "name": {"column_type": PrimitiveType.STRING, "is_primary_key": False, "type": FieldType.COLUMN},
            },
        )

        # cart
        cls.collection_cart = cls._create_collection(
            "cart",
            {
                "id": {
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": True,
                    "type": FieldType.COLUMN,
                    "filter_operators": set([Operator.IN, Operator.EQUAL]),
                },
                "name": {"column_type": PrimitiveType.STRING, "is_primary_key": False, "type": FieldType.COLUMN},
            },
        )

        # product
        cls.collection_product = cls._create_collection(
            "product",
            {
                "id": {
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": True,
                    "type": FieldType.COLUMN,
                    "filter_operators": set([Operator.IN, Operator.EQUAL]),
                },
                "name": {"column_type": PrimitiveType.STRING, "is_primary_key": False, "type": FieldType.COLUMN},
                "tags": {
                    "type": FieldType.POLYMORPHIC_ONE_TO_MANY,
                    "foreign_collection": "tag",
                    "origin_key": "taggable_id",
                    "origin_key_target": "id",
                    "origin_type_field": "taggable_type",
                    "origin_type_value": "product",
                },
            },
        )

        # tag
        cls.collection_tag = cls._create_collection(
            "tag",
            {
                "id": {
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": True,
                    "type": FieldType.COLUMN,
                    "filter_operators": {Operator.IN, Operator.EQUAL},
                },
                "tag": {"column_type": PrimitiveType.STRING, "is_primary_key": False, "type": FieldType.COLUMN},
                "taggable_id": {"column_type": PrimitiveType.NUMBER, "type": FieldType.COLUMN},
                "taggable_type": {
                    "column_type": PrimitiveType.STRING,
                    "type": FieldType.COLUMN,
                    "enum_values": ["product", "order"],
                },
                "taggable": {
                    "type": FieldType.POLYMORPHIC_MANY_TO_ONE,
                    "foreign_collections": ["product", "order"],
                    "foreign_key_target": {"order": "id", "product": "id"},
                    "foreign_key": "taggable_id",
                    "foreign_key_type_field": "taggable_type",
                },
            },
        )

        # to test with uuid
        cls.collection_book = cls._create_collection(
            "book",
            {
                "id": {
                    "column_type": PrimitiveType.UUID,
                    "is_primary_key": True,
                    "type": FieldType.COLUMN,
                    "filter_operators": {Operator.IN, Operator.EQUAL},
                },
                "name": {
                    "column_type": PrimitiveType.STRING,
                    "is_primary_key": False,
                    "type": FieldType.COLUMN,
                    "filter_operators": {Operator.IN, Operator.EQUAL},
                },
                "author_id": {
                    "column_type": PrimitiveType.UUID,
                    "type": FieldType.COLUMN,
                    "filter_operators": {Operator.IN, Operator.EQUAL},
                },
                "author": {
                    "type": FieldType.MANY_TO_ONE,
                    "foreign_collection": "author",
                    "foreign_key_target": "id",
                    "foreign_key": "author_id",
                },
            },
        )
        cls.collection_author = cls._create_collection(
            "Author",
            {
                "id": {
                    "column_type": PrimitiveType.UUID,
                    "is_primary_key": True,
                    "type": FieldType.COLUMN,
                    "filter_operators": {Operator.IN, Operator.EQUAL},
                },
                "name": {
                    "column_type": PrimitiveType.STRING,
                    "is_primary_key": False,
                    "type": FieldType.COLUMN,
                    "filter_operators": {Operator.IN, Operator.EQUAL},
                },
            },
        )

        # str as pk for url encoding

        cls.collection_str_pk = cls._create_collection(
            "StrPK",
            {
                "pk": {
                    "column_type": PrimitiveType.STRING,
                    "is_primary_key": True,
                    "type": FieldType.COLUMN,
                    "is_read_only": False,
                    "default_value": None,
                    "enum_values": None,
                    "filter_operators": set([Operator.EQUAL, Operator.IN]),
                    "is_sortable": True,
                    "validations": [],
                },
                "name": {
                    "column_type": "String",
                    "type": "Column",
                },
            },
        )

    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.options = Options(
            auth_secret="fake_secret",
            env_secret="fake_secret",
            server_url="http://fake:5000",
            prefix="",
            is_production=False,
        )
        # cls.datasource = Mock(Datasource)
        cls.datasource = Datasource(["db_connection"])
        cls.datasource_composite = CompositeDatasource()
        cls.datasource.get_collection = lambda x: cls.datasource._collections[x]
        cls._create_collections()
        cls.datasource._collections = {
            "order": cls.collection_order,
            "status": cls.collection_status,
            "cart": cls.collection_cart,
            "product": cls.collection_product,
            "tag": cls.collection_tag,
            # for uuid
            "author": cls.collection_author,
            "StrPK": cls.collection_str_pk,
        }
        cls.datasource_composite.add_datasource(cls.datasource)

    def setUp(self):
        self.ip_white_list_service = Mock(IpWhiteListService)
        self.ip_white_list_service.is_enable = AsyncMock(return_value=False)

        self.permission_service = Mock(PermissionService)
        self.permission_service.get_scope = AsyncMock(return_value=ConditionTreeLeaf("id", Operator.GREATER_THAN, 0))
        self.permission_service.can = AsyncMock(return_value=None)
        self.permission_service.can_live_query_segment = AsyncMock(return_value=None)

    # dispatch
    def test_dispatch(self):
        request = Request(
            method=RequestMethod.GET,
            query={
                "collection_name": "order",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        crud_resource.get = AsyncMock()
        crud_resource.list = AsyncMock()
        crud_resource.csv = AsyncMock()
        crud_resource.count = AsyncMock()
        crud_resource.add = AsyncMock()
        crud_resource.update = AsyncMock()
        crud_resource.delete = AsyncMock()
        crud_resource.delete_list = AsyncMock()

        self.loop.run_until_complete(crud_resource.dispatch(request, "get"))
        crud_resource.get.assert_called_once()

        self.loop.run_until_complete(crud_resource.dispatch(request, "list"))
        crud_resource.list.assert_called_once()

        self.loop.run_until_complete(crud_resource.dispatch(request, "count"))
        crud_resource.count.assert_called_once()

        self.loop.run_until_complete(crud_resource.dispatch(request, "add"))
        crud_resource.add.assert_called_once()

        self.loop.run_until_complete(crud_resource.dispatch(request, "update"))
        crud_resource.update.assert_called_once()

        self.loop.run_until_complete(crud_resource.dispatch(request, "delete"))
        crud_resource.delete.assert_called_once()

        self.loop.run_until_complete(crud_resource.dispatch(request, "delete_list"))
        crud_resource.delete_list.assert_called_once()

        self.loop.run_until_complete(crud_resource.dispatch(request, "csv"))
        crud_resource.csv.assert_called_once()

    @patch("forestadmin.agent_toolkit.resources.collections.crud.RequestCollection")
    def test_dispatch_error(self, mock_request_collection: Mock):
        request = Request(
            method=RequestMethod.GET,
            query={
                "collection": "order",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        crud_resource.get = AsyncMock()

        with patch.object(
            mock_request_collection, "from_request", side_effect=RequestCollectionException("test exception")
        ):
            response = self.loop.run_until_complete(crud_resource.dispatch(request, "get"))
        assert response.status == 500
        assert json.loads(response.body)["errors"][0] == {
            "name": "RequestCollectionException",
            "detail": "🌳🌳🌳test exception",
            "status": 500,
        }

        # Validation Exception
        with patch.object(crud_resource, "add", side_effect=ValidationError("test exception")):
            response = self.loop.run_until_complete(crud_resource.dispatch(request, "add"))
        assert response.status == 400
        body = json.loads(response.body)
        assert body["errors"][0] == {"name": "ValidationError", "detail": "test exception", "status": 400, "data": {}}

    # get
    def test_get_should_return_simple_data(self):
        mock_order = {"id": 10, "cost": 0, "important": True}

        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={"collection_name": "order", "pks": "10", "fields[order]": "id,cost,important"},
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        with patch.object(
            self.collection_order, "list", new_callable=AsyncMock, return_value=[mock_order]
        ) as mock_list:
            response = self.loop.run_until_complete(crud_resource.get(request))
            mock_list.assert_any_await(
                request.user,
                PaginatedFilter(
                    {
                        "condition_tree": ConditionTreeBranch(
                            "and", [ConditionTreeLeaf("id", "equal", 10), ConditionTreeLeaf("id", "greater_than", 0)]
                        )
                    }
                ),
                ["id", "cost", "important"],
            )
        self.permission_service.can.assert_any_await(request.user, request.collection, "read")
        self.permission_service.can.reset_mock()
        response_content = json.loads(response.body)
        self.assertEqual(response.status, 200)
        self.assertTrue(isinstance(response_content["data"], dict))
        self.assertEqual(response_content["data"]["attributes"]["cost"], mock_order["cost"])
        self.assertEqual(response_content["data"]["attributes"]["important"], mock_order["important"])
        self.assertEqual(response_content["data"]["id"], mock_order["id"])
        # relations

    def test_get_should_return_simple_data_with_relation(self):
        mock_order = {"id": 10, "cost": 200.3, "cart": {"id": 11}, "important": True}
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            headers={},
            client_ip="127.0.0.1",
            query={"collection_name": "order", "pks": "10", "fields[order]": "id,cost,important", "fields[cart]": "id"},
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )

        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud.JsonApiSerializer", wraps=JsonApiSerializer
        ) as spy_jsonapi:
            with patch.object(
                self.collection_order, "list", new_callable=AsyncMock, return_value=[mock_order]
            ) as mock_list:
                response = self.loop.run_until_complete(crud_resource.get(request))
                mock_list.assert_any_await(
                    request.user,
                    PaginatedFilter(
                        {
                            "condition_tree": ConditionTreeBranch(
                                "and",
                                [ConditionTreeLeaf("id", "equal", 10), ConditionTreeLeaf("id", "greater_than", 0)],
                            )
                        }
                    ),
                    ["id", "cost", "important"],
                )
            spy_jsonapi.assert_called_once_with(ANY, ["id", "cost", "important", "products:id"])

        self.permission_service.can.assert_any_await(request.user, request.collection, "read")
        self.permission_service.can.reset_mock()
        response_content = json.loads(response.body)
        self.assertEqual(response.status, 200)
        self.assertTrue(isinstance(response_content["data"], dict))
        self.assertEqual(response_content["data"]["attributes"]["cost"], mock_order["cost"])
        self.assertEqual(
            response_content["data"]["relationships"]["products"],
            {"data": [], "links": {"related": {"href": "/forest/order/10/relationships/products"}}},
        )
        self.assertEqual(response_content["data"]["id"], mock_order["id"])

    def test_get_no_data(self):
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={"collection_name": "order", "pks": "10", "fields[order]": "id,cost"},
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )

        with patch.object(self.collection_order, "list", new_callable=AsyncMock, return_value=[]) as mock_list:
            response = self.loop.run_until_complete(crud_resource.get(request))
            mock_list.assert_any_await(request.user, ANY, Projection("id", "cost"))
        self.permission_service.can.assert_any_await(request.user, request.collection, "read")
        self.permission_service.can.reset_mock()

        self.assertEqual(response.status, 404)
        self.assertIsNone(response.body)

    def test_get_projection_error(self):
        mock_order = {"id": 10, "costt": 200}
        self.collection_order.list = AsyncMock(return_value=[mock_order])
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={"collection_name": "order", "pks": "10", "fields[order]": "id,costt"},
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        with patch.object(self.collection_order, "list", new_callable=AsyncMock, return_value=[]) as mock_list:
            self.assertRaisesRegex(
                CollectionException,
                r"🌳🌳🌳Field not found 'order\.costt'",
                self.loop.run_until_complete,
                crud_resource.get(request),
            )
            mock_list.assert_not_awaited()

        self.permission_service.can.assert_any_await(request.user, request.collection, "read")
        self.permission_service.can.reset_mock()

    def test_get_error_on_unpacking_id(self):
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={"collection_name": "order", "pks": "10", "fields[order]": "id,costt"},
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )

        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud.unpack_id", side_effect=CollectionResourceException
        ) as mocked_unpack_id:
            response = self.loop.run_until_complete(crud_resource.get(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "read")
        self.permission_service.can.reset_mock()
        self.assertEqual(response.status, 500)
        response_content = json.loads(response.body)
        self.assertEqual(
            response_content["errors"][0],
            {
                "name": "CollectionResourceException",
                "detail": "🌳🌳🌳",
                "status": 500,
            },
        )
        mocked_unpack_id.assert_called_once()

    def test_get_should_return_to_many_relations_as_link(self):
        mock_orders = [{"id": 10, "cost": 200}]
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
                "fields[status]": "id",
                "pks": "10",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        with patch.object(self.collection_order, "list", new_callable=AsyncMock, return_value=mock_orders):
            response = self.loop.run_until_complete(crud_resource.get(request))

        response_body = json.loads(response.body)
        self.assertIn("relationships", response_body["data"].keys())
        self.assertEqual(
            response_body["data"]["relationships"],
            {
                "products": {
                    "links": {"related": {"href": "/forest/order/10/relationships/products"}},
                    "data": [],
                }
            },
        )

    def test_get_with_polymorphic_relation_should_add_projection_star(self):
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_tag,
            query={"collection_name": "tag", "pks": "10"},
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        with patch.object(
            self.collection_tag,
            "list",
            new_callable=AsyncMock,
            return_value=[
                {"id": 10, "taggable_id": 10, "taggable_type": "product", "taggable": {"id": 10, "name": "my product"}}
            ],
        ) as mock_list:
            response = self.loop.run_until_complete(crud_resource.get(request))
            mock_list.assert_awaited_with(
                request.user, ANY, ["id", "tag", "taggable_id", "taggable_type", "taggable:*"]
            )

        response_content = json.loads(response.body)
        self.assertEqual(
            response_content,
            {
                "data": {
                    "id": 10,
                    "attributes": {"id": 10, "taggable_id": 10, "taggable_type": "product"},
                    "links": {"self": "/forest/tag/10"},
                    "relationships": {
                        "taggable": {
                            "data": {"id": "10", "type": "product"},
                            "links": {"related": {"href": "/forest/tag/10/relationships/taggable"}},
                        }
                    },
                    "type": "tag",
                },
                "links": {"self": "/forest/tag/10"},
                "included": [
                    {
                        "type": "product",
                        "id": 10,
                        "attributes": {"id": 10, "name": "my product"},
                        "links": {"self": "/forest/product/10"},
                        "relationships": {
                            "tags": {"links": {"related": {"href": "/forest/product/10/relationships/tags"}}}
                        },
                    }
                ],
            },
        )

    def test_get_should_work_when_primary_key_is_url_encoded(self):

        request = RequestCollection(
            RequestMethod.GET,
            self.collection_str_pk,
            query={"collection_name": "StrPK", "pks": "hello%2Fworld"},
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        with patch.object(
            self.collection_str_pk,
            "list",
            new_callable=AsyncMock,
            return_value=[{"pk": "hello/world", "name": "hello world"}],
        ) as mock_list:
            response = self.loop.run_until_complete(crud_resource.get(request))
            mock_list.assert_awaited_with(
                request.user,
                PaginatedFilter(
                    {
                        "condition_tree": ConditionTreeBranch(
                            "and",
                            [
                                ConditionTreeLeaf("pk", "equal", "hello/world"),
                                ConditionTreeLeaf("id", "greater_than", 0),
                            ],
                        )
                    }
                ),
                ANY,
            )
        body_content = json.loads(response.body)
        self.assertEqual(
            body_content,
            {
                "data": {
                    "id": "hello%2Fworld",
                    "attributes": {"pk": "hello/world"},
                    "links": {"self": "/forest/StrPK/hello%2Fworld"},
                    "type": "StrPK",
                },
                "links": {"self": "/forest/StrPK/hello%2Fworld"},
            },
        )

    # add
    def test_simple_add(self):
        mock_order = {"cost": 200}

        request = RequestCollection(
            RequestMethod.POST,
            self.collection_order,
            body={"data": {"attributes": mock_order}, "type": "order"},
            query={"collection_name": "order"},
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )

        with patch.object(
            self.collection_order, "create", new_callable=AsyncMock, return_value=[{**mock_order, "id": 10}]
        ) as mock_collection_create:
            response = self.loop.run_until_complete(crud_resource.add(request))

            mock_collection_create.assert_any_await(request.user, [mock_order])
        self.permission_service.can.assert_any_await(request.user, request.collection, "add")
        self.permission_service.can.reset_mock()

        response_content = json.loads(response.body)
        self.assertEqual(response.status, 200)
        self.assertTrue(isinstance(response_content["data"], dict))
        self.assertEqual(response_content["data"]["attributes"]["cost"], mock_order["cost"])
        self.assertEqual(response_content["data"]["id"], 10)
        self.assertEqual(response_content["data"]["type"], "order")

    def test_add_error_on_json_api(self):
        request = RequestCollection(
            RequestMethod.POST,
            self.collection_order,
            body={"data": {"attributes": {"costtt": 399}}, "type": "order"},
            query={"collection_name": "order"},
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )

        # JsonApiException
        response = self.loop.run_until_complete(crud_resource.add(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "add")
        self.permission_service.can.reset_mock()

        self.assertEqual(response.status, 500)
        response_content = json.loads(response.body)
        self.assertEqual(
            response_content["errors"][0],
            {
                "name": "JsonApiDeserializerException",
                "detail": "🌳🌳🌳Field costtt doesn't exists in collection order.",
                "status": 500,
            },
        )

    def test_add_error_record_validation(self):
        request = RequestCollection(
            RequestMethod.POST,
            self.collection_order,
            body={"data": {"attributes": {}}, "type": "order"},
            query={"collection_name": "order"},
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )

        # RecordValidatorException
        response = self.loop.run_until_complete(crud_resource.add(request))
        self.assertEqual(response.status, 500)
        response_content = json.loads(response.body)
        self.assertEqual(
            response_content["errors"][0],
            {
                "name": "RecordValidatorException",
                "detail": "🌳🌳🌳The record data is empty",
                "status": 500,
            },
        )

    def test_add_error_on_datasource_create(self):
        request = RequestCollection(
            RequestMethod.POST,
            self.collection_order,
            body={"data": {"attributes": {"cost": 399}}, "type": "order"},
            query={"collection_name": "order"},
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )

        # DatasourceException
        with patch.object(self.collection_order, "create", new_callable=AsyncMock, side_effect=DatasourceException):
            response = self.loop.run_until_complete(crud_resource.add(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "add")
        self.permission_service.can.reset_mock()
        self.assertEqual(response.status, 500)
        response_content = json.loads(response.body)
        self.assertEqual(
            response_content["errors"][0],
            {
                "name": "DatasourceException",
                "detail": "🌳🌳🌳",
                "status": 500,
            },
        )

    def test_add_error_on_link_one_to_one_relations(self):
        request = RequestCollection(
            RequestMethod.POST,
            self.collection_order,
            body={
                "data": {
                    "attributes": {"cost": 399},
                    "relationships": {
                        "cart": {"data": {"type": "cart", "id": "11"}},
                    },
                },
                "type": "order",
            },
            query={"collection_name": "order"},
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        # CollectionResourceException
        with patch.object(
            self.collection_order, "create", new_callable=AsyncMock, return_value=[{"cost": 399, "id": 1}]
        ):
            with patch.object(
                self.collection_cart,
                "update",
                new_callable=AsyncMock,
            ):
                response = self.loop.run_until_complete(crud_resource.add(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "add")
        self.permission_service.can.reset_mock()
        self.assertEqual(response.status, 500)
        response_content = json.loads(response.body)
        self.assertEqual(
            response_content["errors"][0],
            {
                "name": "CollectionResourceException",
                "detail": "🌳🌳🌳Missing timezone",
                "status": 500,
            },
        )

    def test_add_with_relation(self):
        request = RequestCollection(
            RequestMethod.POST,
            self.collection_order,
            body={
                "data": {
                    "attributes": {"cost": 200},
                    "relationships": {
                        "cart": {"data": {"type": "cart", "id": "11"}},
                        "status": {"data": {"type": "status", "id": "11"}},
                    },
                },
                "type": "order",
            },
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )

        mock_order = {"id": 10, "cost": 200, "status_id": 11}
        with patch.object(
            self.collection_order,
            "create",
            new_callable=AsyncMock,
            return_value=[mock_order],
        ) as mock_collection_order_create:
            with patch.object(
                self.collection_cart,
                "update",
                new_callable=AsyncMock,
            ) as mock_collection_cart_update:
                response = self.loop.run_until_complete(crud_resource.add(request))

                mock_collection_order_create.assert_any_await(request.user, [{"cost": 200, "status_id": 11}])
                mock_collection_cart_update.assert_any_await(
                    request.user,
                    Filter(
                        {
                            "condition_tree": ConditionTreeBranch(
                                "and",
                                [
                                    ConditionTreeLeaf("order_id", "equal", 10),
                                    ConditionTreeLeaf("id", "greater_than", 0),
                                ],
                            ),
                            "timezone": zoneinfo.ZoneInfo(key="Europe/Paris"),
                        }
                    ),
                    {"order_id": None},
                )
                mock_collection_cart_update.assert_any_await(
                    request.user,
                    Filter(
                        {
                            "condition_tree": ConditionTreeBranch(
                                "and",
                                [ConditionTreeLeaf("id", "equal", 11), ConditionTreeLeaf("id", "greater_than", 0)],
                            ),
                            "timezone": zoneinfo.ZoneInfo(key="Europe/Paris"),
                        }
                    ),
                    {"order_id": 10},
                )
        self.permission_service.can.assert_any_await(request.user, request.collection, "add")
        self.permission_service.can.reset_mock()

        response_content = json.loads(response.body)
        self.assertEqual(response.status, 200)
        self.assertTrue(isinstance(response_content["data"], dict))
        self.assertEqual(response_content["data"]["attributes"]["cost"], mock_order["cost"])
        self.assertEqual(response_content["data"]["id"], mock_order["id"])
        self.assertEqual(response_content["data"]["type"], "order")
        self.assertEqual(response_content["data"]["attributes"]["status_id"], mock_order["status_id"])

    def test_add_should_create_and_associate_polymorphic_many_to_one(self):
        request = RequestCollection(
            RequestMethod.POST,
            self.collection_tag,
            body={
                "data": {
                    "attributes": {"tag": "Good"},
                    "relationships": {"taggable": {"data": {"type": "order", "id": "14"}}},
                },
            },  # body
            query={
                "collection_name": "tag",
                "timezone": "Europe/Paris",
            },  # query
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )

        with patch.object(
            self.collection_tag,
            "create",
            new_callable=AsyncMock,
            return_value=[{"taggable_id": 14, "taggable_type": "order", "tag": "Good", "id": 1}],
        ) as mock_collection_create:
            self.loop.run_until_complete(crud_resource.add(request))
            mock_collection_create.assert_awaited_once_with(
                ANY, [{"taggable_id": 14, "taggable_type": "order", "tag": "Good"}]
            )

    def test_add_should_return_to_many_relations_as_link(self):
        mock_orders = [{"cost": 12.3, "important": True, "id": 10}]
        request = RequestCollection(
            RequestMethod.POST,
            self.collection_order,
            body={
                "data": {
                    "attributes": {"cost": 12.3, "important": True},
                },
            },  # body
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        with patch.object(self.collection_order, "create", new_callable=AsyncMock, return_value=mock_orders):
            response = self.loop.run_until_complete(crud_resource.add(request))

        response_body = json.loads(response.body)
        self.assertIn("relationships", response_body["data"].keys())
        self.assertEqual(
            response_body["data"]["relationships"],
            {
                "products": {
                    "links": {"related": {"href": "/forest/order/10/relationships/products"}},
                    "data": [],
                }
            },
        )

    def test_add_with_uuid_should_work_with_uuid_as_obj_or_str(self):
        for uuid in ["123e4567-e89b-12d3-a456-426614174000", UUID("123e4567-e89b-12d3-a456-426614174000")]:
            request = RequestCollection(
                RequestMethod.POST,
                self.collection_book,
                body={
                    "data": {
                        "attributes": {"name": "Foundation", "id": uuid, "author_id": uuid},
                        "relationships": {},
                    },
                    "type": "book",
                },
                query={
                    "collection_name": "book",
                    "timezone": "Europe/Paris",
                },
                headers={},
                client_ip="127.0.0.1",
            )
            crud_resource = CrudResource(
                self.datasource_composite,
                self.datasource,
                self.permission_service,
                self.ip_white_list_service,
                self.options,
            )
            with patch.object(
                self.collection_book,
                "create",
                new_callable=AsyncMock,
                return_value=[{"name": "Foundation", "id": str(uuid), "author_id": str(uuid)}],
            ) as mock_create:
                self.loop.run_until_complete(crud_resource.add(request))
                mock_create.assert_any_await(
                    FAKE_USER,
                    [
                        {
                            "name": "Foundation",
                            "id": UUID("123e4567-e89b-12d3-a456-426614174000"),
                            "author_id": UUID("123e4567-e89b-12d3-a456-426614174000"),
                        }
                    ],
                )

    # list
    def test_list(self):
        mock_orders = [{"id": 10, "cost": 200}, {"id": 11, "cost": 201}]

        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
                "search": "20",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        self.collection_order.list = AsyncMock(return_value=mock_orders)

        response = self.loop.run_until_complete(crud_resource.list(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "browse")
        self.permission_service.can.reset_mock()

        self.assertEqual(response.status, 200)
        response_content = json.loads(response.body)
        self.assertTrue(isinstance(response_content["data"], list))
        self.assertEqual(len(response_content["data"]), 2)
        self.assertEqual(response_content["data"][0]["type"], "order")
        self.assertEqual(response_content["data"][0]["attributes"]["cost"], mock_orders[0]["cost"])
        self.assertEqual(response_content["data"][0]["id"], mock_orders[0]["id"])
        self.assertEqual(response_content["data"][1]["type"], "order")
        self.assertEqual(response_content["data"][1]["attributes"]["cost"], mock_orders[1]["cost"])
        self.assertEqual(response_content["data"][1]["id"], mock_orders[1]["id"])
        self.collection_order.list.assert_awaited()

        self.assertEqual(response_content["meta"]["decorators"]["0"], {"id": 10, "search": ["cost"]})
        self.assertEqual(response_content["meta"]["decorators"]["1"], {"id": 11, "search": ["cost"]})

    def test_list_should_return_to_many_relations_as_link(self):
        mock_orders = [{"id": 10, "cost": 200}, {"id": 11, "cost": 201}]
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        with patch.object(self.collection_order, "list", new_callable=AsyncMock, return_value=mock_orders):
            response = self.loop.run_until_complete(crud_resource.list(request))

        response_body = json.loads(response.body)
        for record in response_body["data"]:
            self.assertIn("relationships", record.keys())
            self.assertEqual(
                record["relationships"],
                {
                    "products": {
                        "links": {"related": {"href": f"/forest/order/{record['id']}/relationships/products"}},
                        "data": [],
                    }
                },
            )

    def test_list_with_polymorphic_many_to_one_should_query_all_relation_record_columns(self):
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_tag,
            query={
                "collection_name": "tag",
                "fields[tags]": "id,taggable,taggable_id,taggable_type",
                "timezone": "Europe/Paris",
            },
            headers={},
            client_ip="127.0.0.1",
        )

        with patch.object(
            self.collection_tag,
            "list",
            new_callable=AsyncMock,
            return_value=[
                {"id": 1, "taggable_id": 11, "taggable_type": "order", "taggable": {"id": 12, "cost": 12.3}},
            ],
        ) as mock_list:
            self.loop.run_until_complete(crud_resource.list(request))
            mock_list.assert_awaited_once()
            list_args = mock_list.await_args_list[0].args
            self.assertIn("taggable:*", list_args[2])

    def test_list_should_parse_multi_field_sorting(self):
        mock_orders = [
            {"id": 10, "cost": 200, "important": True},
            {"id": 11, "cost": 201, "important": True},
            {"id": 13, "cost": 20, "important": False},
        ]
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost,important",
                "search": "20",
                "sort": "important,-cost",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        self.collection_order.list = AsyncMock(return_value=mock_orders)
        self.loop.run_until_complete(crud_resource.list(request))

        self.collection_order.list.assert_awaited()

        paginated_filter = self.collection_order.list.await_args[0][1]
        self.assertEqual(len(paginated_filter.sort), 2)
        self.assertEqual(paginated_filter.sort[0], {"field": "important", "ascending": True})
        self.assertEqual(paginated_filter.sort[1], {"field": "cost", "ascending": False})

    def test_list_should_handle_live_query_segment(self):
        mock_orders = [{"id": 10, "cost": 200}, {"id": 11, "cost": 201}]

        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
                "search": "test",
                "segmentName": "test_live_query",
                "segmentQuery": "select id from order where important is true;",
                "connectionName": "db_connection",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        self.collection_order.list = AsyncMock(return_value=mock_orders)

        with patch.object(
            crud_resource, "_handle_live_query_segment", new_callable=AsyncMock
        ) as mock_handle_live_queries:
            self.loop.run_until_complete(crud_resource.list(request))
            mock_handle_live_queries.assert_awaited_once_with(request, ConditionTreeLeaf("id", "greater_than", 0))

    def test_list_errors_filter_error(self):
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={
                "collection_name": "order",
                "fields[order]": "id,cost",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )

        # FilterException
        response = self.loop.run_until_complete(crud_resource.list(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "browse")
        self.permission_service.can.reset_mock()

        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "FilterException",
            "detail": "🌳🌳🌳Missing timezone",
            "status": 500,
        }

    def test_list_errors_datasource_error(self):
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={
                "collection_name": "order",
                "fields[order]": "id,cost",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        # DatasourceException
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud.parse_projection_with_pks",
            side_effect=DatasourceException,
        ):
            response = self.loop.run_until_complete(crud_resource.list(request))

        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "DatasourceException",
            "detail": "🌳🌳🌳",
            "status": 500,
        }

    def test_list_errors_jsonapi_error(self):
        mock_orders = [{"id": 10, "cost": 200}, {"id": 11, "cost": 201}]
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={
                "collection_name": "order",
                "fields[order]": "id,cost",
                "timezone": "Europe/Paris",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        # JsonApiException

        self.collection_order.list = AsyncMock(return_value=mock_orders)
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud.JsonApiSerializer.serialize",
            side_effect=JsonApiSerializerException,
        ) as mock_serialize:
            response = self.loop.run_until_complete(crud_resource.list(request))
            mock_serialize.assert_called()
        self.permission_service.can.assert_any_await(request.user, request.collection, "browse")
        self.permission_service.can.reset_mock()

        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "JsonApiSerializerException",
            "detail": "🌳🌳🌳",
            "status": 500,
        }

        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        with patch.object(self.collection_order, "list", new_callable=AsyncMock, return_value=mock_orders):
            response = self.loop.run_until_complete(crud_resource.list(request))

    # count
    def test_count(self):
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={"collection_name": "order", "timezone": "Europe/Paris"},
            headers={},
            client_ip="127.0.0.1",
        )
        self.collection_order.aggregate = AsyncMock(return_value=[{"value": 1000, "group": {}}])
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )

        response = self.loop.run_until_complete(crud_resource.count(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "browse")
        self.permission_service.can.reset_mock()

        assert response.status == 200
        response_content = json.loads(response.body)
        assert isinstance(response_content, dict)
        assert response_content["count"] == 1000
        self.collection_order.aggregate.assert_called()

        self.collection_order.aggregate = AsyncMock(return_value=[])
        response = self.loop.run_until_complete(crud_resource.count(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "browse")
        self.permission_service.can.reset_mock()

        assert response.status == 200
        response_content = json.loads(response.body)
        assert response_content["count"] == 0
        self.collection_order.aggregate.assert_called()

    def test_count_should_handle_live_query_segment(self):
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
                "search": "test",
                "segmentName": "test_live_query",
                "segmentQuery": "select id from order where important is true;",
                "connectionName": "db_connection",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        self.collection_order.aggregate = AsyncMock(return_value=[{"value": 1000, "group": {}}])

        with patch.object(
            crud_resource, "_handle_live_query_segment", new_callable=AsyncMock
        ) as mock_handle_live_queries:
            self.loop.run_until_complete(crud_resource.count(request))
            mock_handle_live_queries.assert_awaited_once_with(request, ConditionTreeLeaf("id", "greater_than", 0))

    def test_deactivate_count(self):
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={"collection_name": "order", "timezone": "Europe/Paris"},
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )

        self.collection_order._schema["countable"] = False
        response = self.loop.run_until_complete(crud_resource.count(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "browse")
        self.permission_service.can.reset_mock()
        self.collection_order._schema["countable"] = True

        assert response.status == 200
        response_content = json.loads(response.body)
        assert response_content["meta"]["count"] == "deactivated"

    # edit
    def test_edit(self):
        mock_order = {"id": 10, "cost": 201}
        request = RequestCollection(
            RequestMethod.PUT,
            self.collection_order,
            body={"data": {"attributes": {"cost": 201}, "relationships": {}}},
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "pks": "10",
                "fields[order]": "id,cost",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        self.collection_order.list = AsyncMock(return_value=[mock_order])
        self.collection_order.update = AsyncMock()
        response = self.loop.run_until_complete(crud_resource.update(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()

        self.assertEqual(response.status, 200)
        response_content = json.loads(response.body)
        self.assertTrue(isinstance(response_content["data"], dict))
        self.assertEqual(response_content["data"]["id"], 10)
        self.assertEqual(response_content["data"]["attributes"]["cost"], 201)
        self.collection_order.update.assert_awaited()

    def test_edit_error_no_pk(self):
        mock_order = {"id": 10, "cost": 201}
        self.collection_order.update = AsyncMock()
        self.collection_order.list = AsyncMock(return_value=[mock_order])
        request = RequestCollection(
            RequestMethod.PUT,
            self.collection_order,
            body={"data": {"attributes": {"cost": 201}, "relationships": {}}},
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "pks": "10|é",
                "fields[order]": "id,cost",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )

        # IdException
        response = self.loop.run_until_complete(crud_resource.update(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()
        self.assertEqual(response.status, 500)
        response_content = json.loads(response.body)
        self.assertEqual(
            response_content["errors"][0],
            {
                "detail": "🌳🌳🌳Unable to unpack the id",
                "name": "IdException",
                "status": 500,
            },
        )

    def test_edit_error_jsonapi_deserialization(self):
        self.collection_order.update = AsyncMock()
        request = RequestCollection(
            RequestMethod.PUT,
            self.collection_order,
            body={"data": {"attributes": {"cost": 201}, "relationships": {}}},
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "pks": "10",
                "fields[order]": "id,cost",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )

        # JsonApiException
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud.JsonApiDeserializer.deserialize",
            side_effect=JsonApiSerializerException,
        ) as mock_deserialize:
            response = self.loop.run_until_complete(crud_resource.update(request))
            mock_deserialize.assert_called()

        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()
        self.assertEqual(response.status, 500)
        response_content = json.loads(response.body)
        self.assertEqual(
            response_content["errors"][0],
            {
                "detail": "🌳🌳🌳",
                "name": "JsonApiSerializerException",
                "status": 500,
            },
        )

    def test_edit_error_jsonapi_serialization(self):
        mock_order = {"id": 10, "cost": 201}
        self.collection_order.list = AsyncMock(return_value=[mock_order])
        request = RequestCollection(
            RequestMethod.PUT,
            self.collection_order,
            body={"data": {"attributes": {"cost": 201}, "relationships": {}}},
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "pks": "10",
                "fields[order]": "id,cost",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )

        # JsonApiException
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud.JsonApiSerializer.serialize",
            side_effect=JsonApiSerializerException,
        ) as mock_serialize:
            response = self.loop.run_until_complete(crud_resource.update(request))
            mock_serialize.assert_called()
        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()
        self.assertEqual(response.status, 500)
        response_content = json.loads(response.body)
        self.assertEqual(
            response_content["errors"][0], {"detail": "🌳🌳🌳", "name": "JsonApiSerializerException", "status": 500}
        )

    def test_edit_should_not_throw_and_do_nothing_on_empty_record(self):
        request = RequestCollection(
            RequestMethod.PUT,
            self.collection_order,
            body={"data": {"attributes": {}, "id": 10, "relationships": {}}},
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "pks": "10",
                "fields[order]": "id,cost",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        mock_order = {"id": 10, "cost": 201}
        self.collection_order.list = AsyncMock(return_value=[mock_order])
        self.collection_order.update = AsyncMock()
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )

        response = self.loop.run_until_complete(crud_resource.update(request))
        self.permission_service.can.reset_mock()

        self.collection_order.update.assert_any_await(ANY, ANY, {})

        self.assertEqual(response.status, 200)

    def test_edit_should_not_update_pk_if_not_set_in_attributes(self):
        request = RequestCollection(
            RequestMethod.PUT,
            self.collection_order,
            body={"data": {"attributes": {"cost": 201}, "id": 10, "relationships": {}}},
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "pks": "10",
                "fields[order]": "id,cost",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        mock_order = {"id": 10, "cost": 201}
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        self.collection_order.list = AsyncMock(return_value=[mock_order])
        self.collection_order.update = AsyncMock()

        self.loop.run_until_complete(crud_resource.update(request))
        self.permission_service.can.reset_mock()
        self.collection_order.update.assert_any_await(ANY, ANY, {"cost": 201})

    def test_edit_should_update_pk_if_set_in_attributes(self):
        request = RequestCollection(
            RequestMethod.PUT,
            self.collection_order,
            body={"data": {"attributes": {"cost": 201, "id": 11}, "id": 10, "relationships": {}}},
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "pks": "10",
                "fields[order]": "id,cost",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        mock_order = {"id": 11, "cost": 201}
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        self.collection_order.list = AsyncMock(return_value=[mock_order])
        self.collection_order.update = AsyncMock()

        self.loop.run_until_complete(crud_resource.update(request))
        self.permission_service.can.reset_mock()
        self.collection_order.update.assert_any_await(ANY, ANY, {"cost": 201, "id": 11})

    def test_update_should_return_to_many_relations_as_link(self):
        mock_orders = [{"cost": 12.3, "important": True, "id": 10}]
        request = RequestCollection(
            RequestMethod.PUT,
            self.collection_order,
            body={
                "data": {
                    "attributes": {"cost": 12.3, "important": True},
                },
            },  # body
            query={
                "collection_name": "order",
                "relation_name": "tags",
                "timezone": "Europe/Paris",
                "pks": "10",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        with patch.object(self.collection_order, "list", new_callable=AsyncMock, return_value=mock_orders):
            response = self.loop.run_until_complete(crud_resource.update(request))

        response_body = json.loads(response.body)
        self.assertIn("relationships", response_body["data"].keys())
        self.assertEqual(
            response_body["data"]["relationships"],
            {
                "products": {
                    "links": {"related": {"href": "/forest/order/10/relationships/products"}},
                    "data": [],
                }
            },
        )

    # delete
    def test_delete(self):
        request = RequestCollection(
            RequestMethod.DELETE,
            self.collection_order,
            query={"collection_name": "order", "timezone": "Europe/Paris", "pks": "10"},
            headers={},
            client_ip="127.0.0.1",
        )
        self.collection_order.delete = AsyncMock()
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        response = self.loop.run_until_complete(crud_resource.delete(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "delete")
        self.permission_service.can.reset_mock()

        assert response.status == 204
        self.collection_order.delete.assert_awaited()

    def test_delete_error(self):
        request = RequestCollection(
            RequestMethod.DELETE,
            self.collection_order,
            query={"collection_name": "order", "timezone": "Europe/Paris", "pks": "10"},
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )

        # CollectionResourceException
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud.unpack_id", side_effect=CollectionResourceException
        ):
            response = self.loop.run_until_complete(crud_resource.delete(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "delete")
        self.permission_service.can.reset_mock()

        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "detail": "🌳🌳🌳",
            "name": "CollectionResourceException",
            "status": 500,
        }

    def test_delete_list(self):
        request = RequestCollection(
            RequestMethod.DELETE,
            self.collection_order,
            body={"data": {"attributes": {"all_records": True, "all_records_ids_excluded": ["10"]}}},
            query={"collection_name": "order", "timezone": "Europe/Paris", "pks": "10"},
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        self.collection_order.delete = AsyncMock()

        response = self.loop.run_until_complete(crud_resource.delete_list(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "delete")
        self.permission_service.can.reset_mock()

        assert response.status == 204
        self.collection_order.delete.assert_awaited()

    # CSV
    def test_csv(self):
        mock_orders = [{"id": 10, "cost": 200}, {"id": 11, "cost": 201}]

        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        self.collection_order.list = AsyncMock(return_value=mock_orders)

        response = self.loop.run_until_complete(crud_resource.csv(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "browse")
        self.permission_service.can.assert_any_await(request.user, request.collection, "export")
        self.permission_service.can.reset_mock()

        assert response.status == 200
        self.collection_order.list.assert_awaited()
        csv_reader = csv.DictReader(response.body)
        response_content = [row for row in csv_reader]
        assert isinstance(response_content, list)
        assert len(response_content) == 2
        assert response_content[0]["cost"] == str(mock_orders[0]["cost"])
        assert response_content[0]["id"] == str(mock_orders[0]["id"])
        assert response_content[1]["cost"] == str(mock_orders[1]["cost"])
        assert response_content[1]["id"] == str(mock_orders[1]["id"])

    def test_csv_errors(self):
        mock_orders = [{"id": 10, "cost": 200}, {"id": 11, "cost": 201}]
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={
                "collection_name": "order",
                "fields[order]": "id,cost",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )

        # FilterException
        response = self.loop.run_until_complete(crud_resource.csv(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "browse")
        self.permission_service.can.assert_any_await(request.user, request.collection, "export")
        self.permission_service.can.reset_mock()

        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "detail": "🌳🌳🌳Missing timezone",
            "name": "FilterException",
            "status": 500,
        }

        # DatasourceException
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud.parse_projection_with_pks",
            side_effect=DatasourceException,
        ):
            response = self.loop.run_until_complete(crud_resource.csv(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "browse")
        self.permission_service.can.assert_any_await(request.user, request.collection, "export")
        self.permission_service.can.reset_mock()

        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {"detail": "🌳🌳🌳", "name": "DatasourceException", "status": 500}

        # CsvException
        self.collection_order.list = AsyncMock(return_value=mock_orders)
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud.Csv.make_csv",
            side_effect=CsvException("cannot make csv"),
        ):
            response = self.loop.run_until_complete(crud_resource.csv(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "browse")
        self.permission_service.can.assert_any_await(request.user, request.collection, "export")
        self.permission_service.can.reset_mock()

        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "detail": "🌳🌳🌳cannot make csv",
            "name": "CsvException",
            "status": 500,
        }

    def test_csv_should_not_apply_pagination(self):
        mock_orders = [{"id": 10, "cost": 200}, {"id": 11, "cost": 201}]

        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        self.collection_order.list = AsyncMock(return_value=mock_orders)

        response = self.loop.run_until_complete(crud_resource.csv(request))
        self.permission_service.can.reset_mock()

        assert response.status == 200
        self.collection_order.list.assert_awaited()
        self.assertIsNone(self.collection_order.list.await_args[0][1].page)
        self.collection_order.list.assert_awaited()
        self.assertIsNone(self.collection_order.list.await_args[0][1].page)

    def test_csv_should_handle_live_query_segment(self):
        mock_orders = [{"id": 10, "cost": 200}, {"id": 11, "cost": 201}]

        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
                "search": "test",
                "segmentName": "test_live_query",
                "segmentQuery": "select id from order where important is true;",
                "connectionName": "db_connection",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        self.collection_order.list = AsyncMock(return_value=mock_orders)

        with patch.object(
            crud_resource, "_handle_live_query_segment", new_callable=AsyncMock
        ) as mock_handle_live_queries:
            self.loop.run_until_complete(crud_resource.csv(request))
            mock_handle_live_queries.assert_awaited_once_with(request, ConditionTreeLeaf("id", "greater_than", 0))

    # live queries

    def test_handle_native_query_should_handle_live_query_segments(self):
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost,important",
                "segmentName": "test_live_query",
                "segmentQuery": "select id from order where important is true;",
                "connectionName": "db_connection",
            },
            headers={},
            client_ip="127.0.0.1",
            user=FAKE_USER,
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        with patch.object(
            self.datasource_composite,
            "execute_native_query",
            new_callable=AsyncMock,
            return_value=[{"id": 10}, {"id": 11}],
        ) as mock_exec_native_query:
            condition_tree = self.loop.run_until_complete(crud_resource._handle_live_query_segment(request, None))
            self.assertEqual(condition_tree, ConditionTreeLeaf("id", "in", [10, 11]))
            mock_exec_native_query.assert_awaited_once_with(
                "db_connection", "select id from order where important is true;", {}
            )

    def test_handle_native_query_should_inject_context_variable_and_handle_like_percent(self):
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost,important",
                "segmentName": "test_live_query",
                "segmentQuery": "select id from user where first_name like 'Ga%' or id = {{currentUser.id}};",
                "connectionName": "db_connection",
            },
            headers={},
            client_ip="127.0.0.1",
            user=FAKE_USER,
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        with patch.object(
            self.permission_service,
            "get_user_data",
            new_callable=AsyncMock,
            return_value={
                "id": 1,
                "firstName": "dummy",
                "lastName": "user",
                "fullName": "dummy user",
                "email": "dummy@user.fr",
                "tags": {},
                "roleId": 8,
                "permissionLevel": "admin",
            },
        ):
            with patch.object(
                self.datasource_composite,
                "execute_native_query",
                new_callable=AsyncMock,
                return_value=[{"id": 10}, {"id": 11}],
            ) as mock_exec_native_query:
                condition_tree = self.loop.run_until_complete(crud_resource._handle_live_query_segment(request, None))
                self.assertEqual(condition_tree, ConditionTreeLeaf("id", "in", [10, 11]))
                mock_exec_native_query.assert_awaited_once_with(
                    "db_connection",
                    "select id from user where first_name like 'Ga\\%' or id = %(currentUser__id)s;",
                    {"currentUser__id": 1},
                )

    def test_handle_native_query_should_intersect_existing_condition_tree(self):
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost,important",
                "segmentName": "test_live_query",
                "segmentQuery": "select id from user where id=10 or id=11;",
                "connectionName": "db_connection",
            },
            headers={},
            client_ip="127.0.0.1",
            user=FAKE_USER,
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        with patch.object(
            self.datasource_composite,
            "execute_native_query",
            new_callable=AsyncMock,
            return_value=[{"id": 10}, {"id": 11}],
        ):
            condition_tree = self.loop.run_until_complete(
                crud_resource._handle_live_query_segment(request, ConditionTreeLeaf("id", "equal", 25))
            )

            self.assertEqual(
                condition_tree,
                ConditionTreeBranch(
                    "and",
                    [
                        ConditionTreeLeaf("id", "equal", 25),
                        ConditionTreeLeaf("id", "in", [10, 11]),
                    ],
                ),
            )

    def test_handle_native_query_should_raise_error_if_live_query_params_are_incorrect(self):
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost,important",
                "segmentName": "test_live_query",
                "segmentQuery": "select id from order where important is true;",
            },
            headers={},
            client_ip="127.0.0.1",
            user=FAKE_USER,
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )

        self.assertRaisesRegex(
            NativeQueryException,
            "Missing native query connection attribute",
            self.loop.run_until_complete,
            crud_resource._handle_live_query_segment(request, None),
        )

        request.query["connectionName"] = None
        self.assertRaisesRegex(
            NativeQueryException,
            "Missing native query connection attribute",
            self.loop.run_until_complete,
            crud_resource._handle_live_query_segment(request, None),
        )

        request.query["connectionName"] = ""
        self.assertRaisesRegex(
            NativeQueryException,
            "Missing native query connection attribute",
            self.loop.run_until_complete,
            crud_resource._handle_live_query_segment(request, None),
        )

    def test_handle_native_query_should_raise_error_if_not_permission(self):
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost,important",
                "segmentName": "test_live_query",
                "segmentQuery": "select id from order where important is true;",
                "connectionName": "db_connection",
            },
            headers={},
            client_ip="127.0.0.1",
            user=FAKE_USER,
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )

        with patch.object(
            self.permission_service,
            "can_live_query_segment",
            new_callable=AsyncMock,
            side_effect=ForbiddenError("You don't have permission to access this segment query."),
        ):
            self.assertRaisesRegex(
                ForbiddenError,
                "You don't have permission to access this segment query.",
                self.loop.run_until_complete,
                crud_resource._handle_live_query_segment(request, None),
            )

    def test_handle_native_query_should_raise_error_if_pk_not_returned(self):
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            query={
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost,important",
                "segmentName": "test_live_query",
                "segmentQuery": "select id as bla, cost from order where important is true;",
                "connectionName": "db_connection",
            },
            headers={},
            client_ip="127.0.0.1",
            user=FAKE_USER,
        )
        crud_resource = CrudResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )
        with patch.object(
            self.datasource_composite,
            "execute_native_query",
            new_callable=AsyncMock,
            return_value=[{"bla": 10, "cost": 100}, {"bla": 11, "cost": 100}],
        ):
            self.assertRaisesRegex(
                NativeQueryException,
                r"Live query must return the primary key field \('id'\).",
                self.loop.run_until_complete,
                crud_resource._handle_live_query_segment(request, None),
            )
