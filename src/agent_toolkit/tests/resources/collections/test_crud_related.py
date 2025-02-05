import asyncio
import csv
import importlib
import json
import sys
from unittest import TestCase
from unittest.mock import ANY, AsyncMock, Mock, patch

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

import forestadmin.agent_toolkit.resources.collections.crud_related
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.resources.collections.exceptions import CollectionResourceException
from forestadmin.agent_toolkit.resources.collections.requests import (
    RequestCollectionException,
    RequestRelationCollection,
)
from forestadmin.agent_toolkit.services.permissions.ip_whitelist_service import IpWhiteListService
from forestadmin.agent_toolkit.services.permissions.permission_service import PermissionService
from forestadmin.agent_toolkit.services.serializers.exceptions import JsonApiSerializerException
from forestadmin.agent_toolkit.utils.context import Request, RequestMethod, User
from forestadmin.agent_toolkit.utils.csv import CsvException
from forestadmin.agent_toolkit.utils.id import unpack_id
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource, DatasourceException
from forestadmin.datasource_toolkit.exceptions import ForbiddenError
from forestadmin.datasource_toolkit.interfaces.fields import (
    FieldType,
    ManyToMany,
    ManyToOne,
    OneToMany,
    OneToOne,
    Operator,
    PrimitiveType,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import Aggregator
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf


def authenticate_mock(fn):
    async def wrapped2(self, request):
        request.user = User(
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

importlib.reload(forestadmin.agent_toolkit.resources.collections.crud_related)
from forestadmin.agent_toolkit.resources.collections.crud_related import CrudRelatedResource  # noqa: E402


class TestCrudRelatedResource(TestCase):
    def mk_request_customer_order_one_to_many(self):
        return [
            self.collection_customer,
            self.collection_order,
            OneToMany(
                {
                    "type": FieldType.ONE_TO_MANY,
                    "foreign_collection": "order",
                    "origin_key": "customer_id",
                    "origin_key_target": "id",
                }
            ),
            "order",
        ]

    def mk_request_order_product_many_to_many(self):
        return [
            self.collection_order,
            self.collection_product,
            ManyToMany(
                {
                    "type": FieldType.MANY_TO_MANY,
                    "through_collection": "product_order",
                    "foreign_collection": "product",
                    "foreign_relation": "product",
                    "foreign_key": "product_id",
                    "foreign_key_target": "id",
                    "origin_key": "order_id",
                    "origin_key_target": "id",
                }
            ),
            "products",
        ]

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
                    "filter_operators": set([Operator.PRESENT, Operator.EQUAL, Operator.IN]),
                },
                "cost": {"column_type": PrimitiveType.NUMBER, "is_primary_key": False, "type": FieldType.COLUMN},
                "products": {
                    "type": FieldType.MANY_TO_MANY,
                    "through_collection": "product_order",
                    "foreign_collection": "product",
                    "foreign_relation": "product",
                    "foreign_key": "product_id",
                    "foreign_key_target": "id",
                    "origin_key": "order_id",
                    "origin_key_target": "id",
                },
                "customer": {
                    "type": FieldType.MANY_TO_ONE,
                    "foreign_collection": "customer",
                    "foreign_key_target": "id",
                    "foreign_key": "customer",
                },
                "customer_id": {
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": False,
                    "type": FieldType.COLUMN,
                },
                "cart": {
                    "type": FieldType.ONE_TO_ONE,
                    "foreign_collection": "cart",
                    "origin_key_target": "id",
                    "origin_key": "order_id",
                },
                "tags": {
                    "type": FieldType.POLYMORPHIC_ONE_TO_MANY,
                    "foreign_collection": "tag",
                    "origin_key": "taggable_id",
                    "origin_key_target": "id",
                    "origin_type_field": "taggable_type",
                    "origin_type_value": "order",
                },
            },
        )

        # product order
        cls.collection_product_order = cls._create_collection(
            "product_order",
            {
                "product_id": {
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": True,
                    "type": FieldType.COLUMN,
                    "filter_operators": set([Operator.PRESENT]),
                },
                "order_id": {
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": True,
                    "type": FieldType.COLUMN,
                    "searchable": True,
                    "segments": [],
                    "filter_operators": set([Operator.PRESENT]),
                },
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
                    "filter_operators": set([Operator.PRESENT]),
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
                    "filter_operators": set([Operator.PRESENT]),
                },
                "name": {"column_type": PrimitiveType.STRING, "is_primary_key": False, "type": FieldType.COLUMN},
            },
        )

        # customers
        cls.collection_customer = cls._create_collection(
            "customer",
            {
                "id": {
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": True,
                    "type": FieldType.COLUMN,
                    "filter_operators": set([Operator.PRESENT]),
                },
                "name": {
                    "column_type": PrimitiveType.STRING,
                    "is_primary_key": False,
                    "type": FieldType.COLUMN,
                    "filter_operators": set([Operator.PRESENT]),
                },
                "order": {
                    "type": FieldType.ONE_TO_MANY,
                    "foreign_collection": "order",
                    "origin_key": "customer_id",
                    "origin_key_target": "id",
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
                "taggable_id": {"column_type": PrimitiveType.NUMBER, "type": FieldType.COLUMN},
                "taggable_type": {
                    "column_type": PrimitiveType.STRING,
                    "type": FieldType.COLUMN,
                    "enum_values": ["customer", "order"],
                },
                "taggable": {
                    "type": FieldType.POLYMORPHIC_MANY_TO_ONE,
                    "foreign_collections": ["customer", "order"],
                    "foreign_key_target": {"order": "id", "customer": "id"},
                    "foreign_key": "taggable_id",
                    "foreign_type_field": "taggable_type",
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
            is_production=False,
        )
        # cls.datasource = Mock(Datasource)
        cls.datasource = Datasource()
        cls.datasource.get_collection = lambda x: cls.datasource._collections[x]
        cls._create_collections()
        cls.datasource._collections = {
            "order": cls.collection_order,
            # "status": cls.collection_status,
            "cart": cls.collection_cart,
            "customer": cls.collection_customer,
            "product": cls.collection_product,
            "product_order": cls.collection_product_order,
        }

    def setUp(self):
        self.ip_white_list_service = Mock(IpWhiteListService)
        self.ip_white_list_service.is_enable = AsyncMock(return_value=False)

        self.permission_service = Mock(PermissionService)
        self.permission_service.can = AsyncMock(return_value=True)
        self.permission_service.get_scope = AsyncMock(return_value=ConditionTreeLeaf("id", Operator.GREATER_THAN, 0))

        self.crud_related_resource = CrudRelatedResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )

    def tearDown(self):
        self.permission_service.can = None

    # -- dispatch
    def test_dispatch(self):
        request = Request(
            method=RequestMethod.GET,
            query={"collection_name": "customer", "relation_name": "order"},
            headers={},
            client_ip="127.0.0.1",
        )

        self.crud_related_resource.list = AsyncMock()
        self.crud_related_resource.csv = AsyncMock()
        self.crud_related_resource.count = AsyncMock()
        self.crud_related_resource.add = AsyncMock()
        self.crud_related_resource.update_list = AsyncMock()
        self.crud_related_resource.delete_list = AsyncMock()

        self.loop.run_until_complete(self.crud_related_resource.dispatch(request, "list"))
        self.crud_related_resource.list.assert_called_once()

        self.loop.run_until_complete(self.crud_related_resource.dispatch(request, "count"))
        self.crud_related_resource.count.assert_called_once()

        self.loop.run_until_complete(self.crud_related_resource.dispatch(request, "add"))
        self.crud_related_resource.add.assert_called_once()

        self.loop.run_until_complete(self.crud_related_resource.dispatch(request, "update_list"))
        self.crud_related_resource.update_list.assert_called_once()

        self.loop.run_until_complete(self.crud_related_resource.dispatch(request, "delete_list"))
        self.crud_related_resource.delete_list.assert_called_once()

        self.loop.run_until_complete(self.crud_related_resource.dispatch(request, "csv"))
        self.crud_related_resource.csv.assert_called_once()

    @patch("forestadmin.agent_toolkit.resources.collections.crud_related.RequestRelationCollection")
    def test_dispatch_error(self, mock_request_relation_collection: Mock):
        request = Request(
            method=RequestMethod.GET,
            query={"collection_name": "customer", "relation_name": "order"},
            headers={},
            client_ip="127.0.0.1",
        )

        self.assertRaises(
            AttributeError, self.loop.run_until_complete, self.crud_related_resource.dispatch(request, "get")
        )

        with patch.object(
            mock_request_relation_collection, "from_request", side_effect=RequestCollectionException("test exception")
        ):
            response = self.loop.run_until_complete(self.crud_related_resource.dispatch(request, "list"))
        self.assertEqual(response.status, 500)

        with patch.object(self.crud_related_resource, "list", side_effect=ForbiddenError("")):
            response = self.loop.run_until_complete(self.crud_related_resource.dispatch(request, "list"))
        self.assertEqual(response.status, 403)

        with patch.object(self.crud_related_resource, "list", side_effect=Exception("")):
            response = self.loop.run_until_complete(self.crud_related_resource.dispatch(request, "list"))
        self.assertEqual(response.status, 500)

    # -- list
    def test_list(self):
        mock_orders = [{"id": 10, "cost": 200}, {"id": 11, "cost": 201}]

        request = RequestRelationCollection(
            RequestMethod.GET,
            *self.mk_request_customer_order_one_to_many(),
            headers={},
            query={
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
                "pks": "2",  # customer id
                "search_extended": "0",
                "search": "20",
            },
            body=None,
            user=None,
            client_ip="127.0.0.1",
        )
        crud_related_resource = CrudRelatedResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )

        with patch.object(
            self.collection_order, "list", new_callable=AsyncMock, return_value=mock_orders
        ) as mocked_collection_list:
            response = self.loop.run_until_complete(crud_related_resource.list(request))
            mocked_collection_list.assert_awaited()

        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "browse")
        self.permission_service.can.reset_mock()

        self.assertEqual(response.status, 200)
        response_content = json.loads(response.body)
        self.assertTrue(isinstance(response_content["data"], list))
        self.assertEqual(len(response_content["data"]), 2)
        self.assertEqual(response_content["data"][0]["attributes"]["cost"], mock_orders[0]["cost"])
        self.assertEqual(response_content["data"][0]["id"], mock_orders[0]["id"])
        self.assertEqual(response_content["data"][0]["type"], "order")
        self.assertEqual(response_content["data"][1]["attributes"]["cost"], mock_orders[1]["cost"])
        self.assertEqual(response_content["data"][1]["id"], mock_orders[1]["id"])
        self.assertEqual(response_content["data"][1]["type"], "order")

        self.assertEqual(response_content["meta"]["decorators"]["0"], {"id": 10, "search": ["cost"]})
        self.assertEqual(response_content["meta"]["decorators"]["1"], {"id": 11, "search": ["cost"]})

    def test_list_error_on_relation_type(self):
        crud_related_resource = CrudRelatedResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )

        # Relation Type
        request = RequestRelationCollection(
            RequestMethod.GET,
            self.collection_customer,
            self.collection_order,
            OneToOne(
                {
                    "type": FieldType.ONE_TO_ONE,
                    "foreign_collection": "order",
                    "origin_key": "customer_id",
                    "origin_key_target": "id",
                }
            ),
            "orders",
            headers={},
            query={},
            client_ip="127.0.0.1",
        )

        response = self.loop.run_until_complete(crud_related_resource.list(request))

        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "browse")
        self.permission_service.can.reset_mock()

        self.assertEqual(response.status, 500)
        response_content = json.loads(response.body)
        self.assertEqual(
            response_content["errors"][0],
            {
                "name": "ForestException",
                "detail": "🌳🌳🌳Unhandled relation type",
                "status": 500,
            },
        )

    def test_list_error_on_instance_pk(self):
        mock_orders = [{"id": 10, "cost": 200}, {"id": 11, "cost": 201}]
        crud_related_resource = CrudRelatedResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )
        # collectionResourceException
        request_get_params = {
            "collection_name": "customer",
            "relation_name": "order",
            "timezone": "Europe/Paris",
            "fields[order]": "id,cost",
            # "pks": "2",  # error on customer id
        }
        request = RequestRelationCollection(
            RequestMethod.GET,
            *self.mk_request_customer_order_one_to_many(),
            query=request_get_params,
            headers={},
            client_ip="127.0.0.1",
        )

        response = self.loop.run_until_complete(crud_related_resource.list(request))

        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "browse")
        self.permission_service.can.reset_mock()

        self.assertEqual(response.status, 500)
        response_content = json.loads(response.body)
        self.assertEqual(
            response_content["errors"][0],
            {
                "name": "CollectionResourceException",
                "detail": "🌳🌳🌳primary keys are missing",
                "status": 500,
            },
        )

    def test_list_error_on_jsonapi_serialize(self):
        mock_orders = [{"id": 10, "cost": 200}, {"id": 11, "cost": 201}]
        crud_related_resource = CrudRelatedResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )
        # collectionResourceException
        request_get_params = {
            "collection_name": "customer",
            "relation_name": "order",
            "timezone": "Europe/Paris",
            "fields[order]": "id,cost",
            "pks": "2",
        }

        # # JsonApiException
        request = RequestRelationCollection(
            RequestMethod.GET,
            *self.mk_request_customer_order_one_to_many(),
            query=request_get_params,
            headers={},
            client_ip="127.0.0.1",
        )
        self.collection_order.list = AsyncMock(return_value=mock_orders)

        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud_related.JsonApiSerializer.serialize",
            side_effect=JsonApiSerializerException,
        ) as mock_serialize:
            response = self.loop.run_until_complete(crud_related_resource.list(request))
            mock_serialize.assert_called()

        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "browse")
        self.permission_service.can.reset_mock()

        self.assertEqual(response.status, 500)
        response_content = json.loads(response.body)
        self.assertEqual(
            response_content["errors"][0],
            {
                "name": "JsonApiSerializerException",
                "detail": "🌳🌳🌳",
                "status": 500,
            },
        )

    # CSV
    def test_csv(self):
        mock_orders = [{"id": 10, "cost": 200}, {"id": 11, "cost": 201}]

        request = RequestRelationCollection(
            RequestMethod.GET,
            *self.mk_request_customer_order_one_to_many(),
            query={
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
                "pks": "2",  # customer id
                "search_extended": "0",
                "search": "20",
            },
            headers={},
            client_ip="127.0.0.1",
        )
        with patch.object(
            self.collection_order, "list", new_callable=AsyncMock, return_value=mock_orders
        ) as mocked_collection_list:
            response = self.loop.run_until_complete(self.crud_related_resource.csv(request))
            mocked_collection_list.assert_awaited()
        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "browse")
        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "export")
        self.permission_service.can.reset_mock()

        assert response.status == 200
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
        crud_related_resource = CrudRelatedResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )

        # Relation Type
        request = RequestRelationCollection(
            RequestMethod.GET,
            self.collection_customer,
            self.collection_order,
            OneToOne(
                {
                    "type": FieldType.ONE_TO_ONE,
                    "foreign_collection": "order",
                    "origin_key": "customer_id",
                    "origin_key_target": "id",
                }
            ),
            "orders",
            query={},
            headers={},
            client_ip="127.0.0.1",
        )
        response = self.loop.run_until_complete(crud_related_resource.csv(request))

        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "browse")
        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "export")
        self.permission_service.can.reset_mock()
        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "ForestException",
            "detail": "🌳🌳🌳Unhandled relation type",
            "status": 500,
        }

        # FilterException
        request_get_params = {
            "collection_name": "customer",
            "relation_name": "order",
            "timezone": "Europe/Paris",
            "fields[order]": "id,cost",
            # "pks": "2",  # error on customer id
        }
        request = RequestRelationCollection(
            RequestMethod.GET,
            *self.mk_request_customer_order_one_to_many(),
            query=request_get_params,
            headers={},
            client_ip="127.0.0.1",
        )
        response = self.loop.run_until_complete(crud_related_resource.csv(request))
        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "browse")
        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "export")
        self.permission_service.can.reset_mock()

        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "CollectionResourceException",
            "detail": "🌳🌳🌳primary keys are missing",
            "status": 500,
        }

        # collectionResourceException
        request_get_params["pks"] = "2"
        request = RequestRelationCollection(
            RequestMethod.GET,
            *self.mk_request_customer_order_one_to_many(),
            query=request_get_params,
            headers={},
            client_ip="127.0.0.1",
        )
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud_related.parse_projection_with_pks",
            side_effect=DatasourceException,
        ):
            response = self.loop.run_until_complete(crud_related_resource.csv(request))
        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "browse")
        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "export")
        self.permission_service.can.reset_mock()

        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "DatasourceException",
            "detail": "🌳🌳🌳",
            "status": 500,
        }

        # JsonApiException
        self.collection_order.list = AsyncMock(return_value=mock_orders)
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud_related.Csv.make_csv",
            side_effect=CsvException("cannot make csv"),
        ):
            response = self.loop.run_until_complete(crud_related_resource.csv(request))

        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "browse")
        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "export")
        self.permission_service.can.reset_mock()

        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "CsvException",
            "detail": "🌳🌳🌳cannot make csv",
            "status": 500,
        }

    def test_csv_should_not_apply_pagination(self):
        mock_orders = [{"id": 10, "cost": 200}, {"id": 11, "cost": 201}]

        request = RequestRelationCollection(
            RequestMethod.GET,
            *self.mk_request_customer_order_one_to_many(),
            headers={},
            client_ip="127.0.0.1",
            query={
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
                "pks": "2",  # customer id
                "search_extended": "0",
                "search": "20",
            },
        )
        with patch.object(
            self.collection_order, "list", new_callable=AsyncMock, return_value=mock_orders
        ) as mocked_collection_list:
            self.loop.run_until_complete(self.crud_related_resource.csv(request))
            mocked_collection_list.assert_awaited()
            self.assertIsNone(mocked_collection_list.await_args[0][1].page)

        self.permission_service.can.reset_mock()

    # add
    def test_add(self):
        # One to Many
        request = RequestRelationCollection(
            RequestMethod.POST,
            *self.mk_request_customer_order_one_to_many(),
            body={"data": [{"id": "201", "type": "order"}]},  # body
            query={
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "pks": "2",  # customer id
            },  # query
            headers={},
            client_ip="127.0.0.1",
        )
        crud_related_resource = CrudRelatedResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )

        with patch.object(self.collection_order, "update", new_callable=AsyncMock) as mock_collection_update:
            response = self.loop.run_until_complete(crud_related_resource.add(request))
            mock_collection_update.assert_awaited()

        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()
        self.assertEqual(response.status, 204)

        # many to Many
        request = RequestRelationCollection(
            RequestMethod.POST,
            *self.mk_request_order_product_many_to_many(),
            body={"data": [{"id": "201", "type": "product"}]},  # body
            query={
                "collection_name": "order",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "pks": "2",  # order id
            },  # query
            headers={},
            client_ip="127.0.0.1",
        )
        crud_related_resource = CrudRelatedResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )

        with patch.object(self.collection_product_order, "create", new_callable=AsyncMock) as mock_collection_create:
            response = self.loop.run_until_complete(crud_related_resource.add(request))

            mock_collection_create.assert_awaited()
        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()

        self.assertEqual(response.status, 204)

    def test_add_should_associate_polymorphic_one_to_many(self):
        request = RequestRelationCollection(
            RequestMethod.POST,
            self.collection_order,
            self.collection_tag,
            self.collection_order.get_field("tags"),
            "tags",
            body={"data": [{"id": "201", "type": "tag"}]},  # body
            query={
                "collection_name": "order",
                "relation_name": "tags",
                "timezone": "Europe/Paris",
                "pks": "2",  # customer id
            },  # query
            headers={},
            client_ip="127.0.0.1",
        )
        crud_related_resource = CrudRelatedResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )

        with patch.object(self.collection_tag, "update", new_callable=AsyncMock) as mock_collection_update:
            self.loop.run_until_complete(crud_related_resource.add(request))
            mock_collection_update.assert_awaited_once()
            self.assertIn(
                ConditionTreeLeaf("id", "equal", 201),
                mock_collection_update.await_args_list[0].args[1].condition_tree.conditions,
            )
            self.assertEqual(
                mock_collection_update.await_args_list[0].args[2], {"taggable_id": 2, "taggable_type": "order"}
            )

    def test_add_error_no_id(self):
        request_get_params = {
            "collection_name": "customer",
            "relation_name": "order",
            "timezone": "Europe/Paris",
            # "pks": "2",  # customer id
        }
        request = RequestRelationCollection(
            RequestMethod.POST,
            *self.mk_request_customer_order_one_to_many(),
            body={"data": [{"id": "201", "type": "order"}]},  # body
            query=request_get_params,  # query
            headers={},
            client_ip="127.0.0.1",
        )

        # no_id exception
        response = self.loop.run_until_complete(self.crud_related_resource.add(request))

        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()

        self.assertEqual(response.status, 500)
        response_content = json.loads(response.body)
        self.assertEqual(
            response_content["errors"][0],
            {
                "name": "CollectionResourceException",
                "detail": "🌳🌳🌳primary keys are missing",
                "status": 500,
            },
        )

    def test_add_error_no_id_in_body(self):
        request_get_params = {
            "collection_name": "customer",
            "relation_name": "order",
            "timezone": "Europe/Paris",
            "pks": "2",  # customer id
        }
        request = RequestRelationCollection(
            RequestMethod.POST,
            *self.mk_request_customer_order_one_to_many(),
            body={"data": [{"id": "201", "type": "order"}]},  # body
            query=request_get_params,  # query
            headers={},
            client_ip="127.0.0.1",
        )

        # no body id
        request = RequestRelationCollection(
            RequestMethod.POST,
            *self.mk_request_customer_order_one_to_many(),
            query=request_get_params,  # query
            headers={},
            client_ip="127.0.0.1",
        )
        response = self.loop.run_until_complete(self.crud_related_resource.add(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()
        self.assertEqual(response.status, 500)
        response_content = json.loads(response.body)
        self.assertEqual(
            response_content["errors"][0],
            {
                "name": "ForestException",
                "detail": "🌳🌳🌳missing target's id",
                "status": 500,
            },
        )

    def test_add_error_unpack_foreign_id(self):
        # unpack foreign id
        request_get_params = {
            "collection_name": "customer",
            "relation_name": "order",
            "timezone": "Europe/Paris",
            "pks": "2",  # customer id
        }
        request = RequestRelationCollection(
            RequestMethod.POST,
            *self.mk_request_customer_order_one_to_many(),
            body={"data": [{"id": "201", "type": "order"}]},  # body
            query=request_get_params,  # query
            headers={},
            client_ip="127.0.0.1",
        )

        def mocked_unpack_id(schema, pk):
            if pk != "201":
                return unpack_id(schema, pk)
            else:
                raise CollectionResourceException()

        with patch("forestadmin.agent_toolkit.resources.collections.crud_related.unpack_id", mocked_unpack_id):
            response = self.loop.run_until_complete(self.crud_related_resource.add(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()
        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "CollectionResourceException",
            "detail": "🌳🌳🌳",
            "status": 500,
        }

    def test_add_error_bad_relation_type(self):
        # Unhandled relation type
        request_get_params = {
            "collection_name": "customer",
            "relation_name": "order",
            "timezone": "Europe/Paris",
            "pks": "2",  # customer id
        }
        request = RequestRelationCollection(
            RequestMethod.POST,
            self.collection_customer,
            self.collection_order,
            OneToOne(
                {
                    "type": FieldType.ONE_TO_ONE,
                    "foreign_collection": "order",
                    "origin_key": "customer_id",
                    "origin_key_target": "id",
                }
            ),
            "orders",
            body={"data": [{"id": "201", "type": "order"}]},  # body
            query=request_get_params,  # query
            headers={},
            client_ip="127.0.0.1",
        )
        response = self.loop.run_until_complete(self.crud_related_resource.add(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()
        self.assertEqual(response.status, 500)
        response_content = json.loads(response.body)
        self.assertEqual(
            response_content["errors"][0],
            {
                "name": "ForestException",
                "detail": "🌳🌳🌳Unhandled relation type",
                "status": 500,
            },
        )

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud_related.ConditionTreeFactory.match_ids",
        return_value=ConditionTreeLeaf("id", Operator.EQUAL, 201),
    )
    def test_edit(self, mocked_match_id: Mock):
        crud_related_resource = CrudRelatedResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )

        # one to one  (order & cart)
        request = RequestRelationCollection(
            RequestMethod.PUT,
            self.collection_order,
            self.collection_cart,
            OneToOne(
                {
                    "type": FieldType.ONE_TO_ONE,
                    "foreign_collection": "cart",
                    "origin_key": "order_id",
                    "origin_key_target": "id",
                }
            ),
            "orders",
            body={"data": {"id": "201", "type": "cart"}},  # body
            query={
                "collection_name": "order",
                "relation_name": "cart",
                "timezone": "Europe/Paris",
                "pks": "2",  # order id
            },  # query
            headers={},
            client_ip="127.0.0.1",
        )

        response = self.loop.run_until_complete(crud_related_resource.update_list(request))
        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "edit")
        self.permission_service.can.reset_mock()

        assert response.status == 204
        self.collection_cart.update.assert_awaited()

        # many to one (order & customer)
        request = RequestRelationCollection(
            RequestMethod.PUT,
            self.collection_order,
            self.collection_customer,
            ManyToOne(
                {
                    "type": FieldType.MANY_TO_ONE,
                    "foreign_collection": "customer",
                    "foreign_key": "customer_id",
                    "foreign_key_target": "id",
                }
            ),
            "orders",
            body={"data": {"id": "201", "type": "customer"}},  # body
            query={
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "pks": "2",  # customer id
            },  # query
            headers={},
            client_ip="127.0.0.1",
        )

        response = self.loop.run_until_complete(crud_related_resource.update_list(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()

        assert response.status == 204
        self.collection_cart.update.assert_awaited()

    def test_edit_relation_with_data_equal_none(self):
        crud_related_resource = CrudRelatedResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )
        query_get_params = {
            "collection_name": "customer",
            "relation_name": "order",
            # "timezone": "Europe/Paris",
            "pks": "2",  # customer id
        }

        request = RequestRelationCollection(
            RequestMethod.PUT,
            self.collection_order,
            self.collection_customer,
            ManyToOne(
                {
                    "type": FieldType.MANY_TO_ONE,
                    "foreign_collection": "customer",
                    "foreign_key": "customer_id",
                    "foreign_key_target": "id",
                }
            ),
            "orders",
            body={"data": None},  # body
            query=query_get_params,  # query
            headers={},
            client_ip="127.0.0.1",
        )

        with patch.object(self.collection_order, "update", new_callable=AsyncMock) as update_order:
            response = self.loop.run_until_complete(crud_related_resource.update_list(request))
            update_order_args = update_order.await_args.args
            self.assertIn(ConditionTreeLeaf("id", "equal", 2), update_order_args[1].condition_tree.conditions)
            self.assertEqual(update_order_args[2], {"customer_id": None})

        self.permission_service.can.assert_awaited_with(ANY, request.collection, "edit")

        self.assertEqual(response.status, 204)

    def test_edit_error(self):
        crud_related_resource = CrudRelatedResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )
        query_get_params = {
            "collection_name": "customer",
            "relation_name": "order",
            # "timezone": "Europe/Paris",
            "pks": "2",  # customer id
        }

        # no id
        del query_get_params["pks"]
        query_get_params["timezone"] = "Europe/Paris"
        request = RequestRelationCollection(
            RequestMethod.PUT,
            self.collection_order,
            self.collection_customer,
            ManyToOne(
                {
                    "type": FieldType.MANY_TO_ONE,
                    "foreign_collection": "customer",
                    "foreign_key": "customer_id",
                    "foreign_key_target": "id",
                }
            ),
            "orders",
            body={"data": {"id": "201", "type": "customer"}},  # body
            query=query_get_params,  # query
            headers={},
            client_ip="127.0.0.1",
        )

        response = self.loop.run_until_complete(crud_related_resource.update_list(request))
        self.permission_service.can.assert_not_awaited()
        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "CollectionResourceException",
            "detail": "🌳🌳🌳primary keys are missing",
            "status": 500,
        }

        # Error in update relation
        query_get_params["pks"] = "2"
        request = RequestRelationCollection(
            RequestMethod.PUT,
            self.collection_order,
            self.collection_customer,
            ManyToOne(
                {
                    "type": FieldType.MANY_TO_ONE,
                    "foreign_collection": "customer",
                    "foreign_key": "customer_id",
                    "foreign_key_target": "id",
                }
            ),
            "orders",
            body={"data": {"id": "201", "type": "customer"}},  # body
            query=query_get_params,  # query
            headers={},
            client_ip="127.0.0.1",
        )

        with patch.object(crud_related_resource, "_update_many_to_one", side_effect=CollectionResourceException):
            response = self.loop.run_until_complete(crud_related_resource.update_list(request))
        self.permission_service.can.assert_not_awaited()
        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "CollectionResourceException",
            "detail": "🌳🌳🌳",
            "status": 500,
        }

        # Unhandled relation
        request = RequestRelationCollection(
            RequestMethod.PUT,
            *self.mk_request_order_product_many_to_many(),
            body={"data": {"id": "201", "type": "customer"}},  # body
            query=query_get_params,  # query
            headers={},
            client_ip="127.0.0.1",
        )
        response = self.loop.run_until_complete(crud_related_resource.update_list(request))
        self.permission_service.can.assert_not_awaited()

        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "ForestException",
            "detail": "🌳🌳🌳Unhandled relation type",
            "status": 500,
        }

    # Count
    def test_count(self):
        request = RequestRelationCollection(
            RequestMethod.GET,
            *self.mk_request_customer_order_one_to_many(),
            query={
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
                "pks": "2",  # customer id
            },
            headers={},
            client_ip="127.0.0.1",
        )

        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud_related.CollectionUtils.aggregate_relation",
            new_callable=AsyncMock,
            return_value=[{"value": 1, "group": {}}],
        ) as mock_aggregate_relation:
            response = self.loop.run_until_complete(self.crud_related_resource.count(request))
            mock_aggregate_relation.assert_awaited()
        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "browse")
        self.permission_service.can.reset_mock()

        assert response.status == 200
        response_content = json.loads(response.body)
        assert response_content["count"] == 1

    def test_deactivate_count(self):
        request = RequestRelationCollection(
            RequestMethod.GET,
            *self.mk_request_customer_order_one_to_many(),
            query={
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
                "pks": "2",  # customer id
            },
            headers={},
            client_ip="127.0.0.1",
        )
        self.collection_order._schema["countable"] = False
        response = self.loop.run_until_complete(self.crud_related_resource.count(request))
        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "browse")
        self.permission_service.can.reset_mock()

        self.collection_order._schema["countable"] = True

        assert response.status == 200
        response_content = json.loads(response.body)
        assert response_content["meta"]["count"] == "deactivated"

    def test_count_error(self):
        query_get_params = {
            "collection_name": "customer",
            "relation_name": "order",
            "timezone": "Europe/Paris",
            "fields[order]": "id,cost",
            # "pks": "2",  # customer id
        }
        request = RequestRelationCollection(
            RequestMethod.GET,
            *self.mk_request_customer_order_one_to_many(),
            query=query_get_params,
            headers={},
            client_ip="127.0.0.1",
        )
        response = self.loop.run_until_complete(self.crud_related_resource.count(request))
        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "browse")
        self.permission_service.can.reset_mock()
        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "CollectionResourceException",
            "detail": "🌳🌳🌳primary keys are missing",
            "status": 500,
        }

        query_get_params["pks"] = "2"
        request = RequestRelationCollection(
            RequestMethod.GET,
            *self.mk_request_customer_order_one_to_many(),
            query=query_get_params,
            headers={},
            client_ip="127.0.0.1",
        )
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud_related.CollectionUtils.aggregate_relation",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_aggregate_relation:
            response = self.loop.run_until_complete(self.crud_related_resource.count(request))
            mock_aggregate_relation.assert_awaited()
        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "browse")
        self.permission_service.can.reset_mock()
        assert response.status == 200
        response_content = json.loads(response.body)
        assert response_content["count"] == 0

    # delete_list
    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud_related.ConditionTreeFactory.match_ids",
        return_value=ConditionTreeLeaf("id", Operator.EQUAL, 201),
    )
    def test_delete_list(self, mock_mach_id: Mock):
        # disassociate one_to_many
        query_get_params = {
            "collection_name": "customer",
            "relation_name": "order",
            "timezone": "Europe/Paris",
            "fields[order]": "id,cost",
            "pks": "2",  # customer id
        }
        request = RequestRelationCollection(
            RequestMethod.DELETE,
            *self.mk_request_customer_order_one_to_many(),
            body={"data": [{"id": "201", "type": "order"}]},
            query=query_get_params,
            headers={},
            client_ip="127.0.0.1",
        )
        with patch.object(
            self.crud_related_resource, "_delete_one_to_many", new_callable=AsyncMock
        ) as fake_delete_one_to_many:
            response = self.loop.run_until_complete(self.crud_related_resource.delete_list(request))
            fake_delete_one_to_many.assert_awaited()
        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()

        assert response.status == 204

        # remove many_to_many
        # many to many (order & products)
        del query_get_params["fields[order]"]
        request = RequestRelationCollection(
            RequestMethod.DELETE,
            *self.mk_request_order_product_many_to_many(),
            body={"data": [{"id": "201", "type": "product"}]},  # body
            query=query_get_params,  # query
            headers={},
            client_ip="127.0.0.1",
        )
        with patch.object(
            self.crud_related_resource, "_delete_many_to_many", new_callable=AsyncMock
        ) as fake_delete_many_to_many:
            response = self.loop.run_until_complete(self.crud_related_resource.delete_list(request))
            fake_delete_many_to_many.assert_awaited()
        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()

        assert response.status == 204

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud_related.ConditionTreeFactory.match_ids",
        return_value=ConditionTreeLeaf("id", Operator.EQUAL, 201),
    )
    def test_delete_list_error(self, mock_mach_id: Mock):
        crud_related_resource = CrudRelatedResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )
        query_get_params = {
            "collection_name": "customer",
            "relation_name": "order",
            "timezone": "Europe/Paris",
            # "pks": "2",  # customer id
        }
        request = RequestRelationCollection(
            RequestMethod.DELETE,
            *self.mk_request_order_product_many_to_many(),
            body={"data": [{"id": "201", "type": "product"}]},  # body
            query=query_get_params,  # query
            headers={},
            client_ip="127.0.0.1",
        )
        response = self.loop.run_until_complete(crud_related_resource.delete_list(request))
        self.permission_service.can.assert_not_awaited()
        self.permission_service.can.reset_mock()
        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "CollectionResourceException",
            "detail": "🌳🌳🌳primary keys are missing",
            "status": 500,
        }

        query_get_params["pks"] = "2"
        request = RequestRelationCollection(
            RequestMethod.DELETE,
            *self.mk_request_order_product_many_to_many(),
            body={"data": [{"id": "201", "type": "product"}]},  # body
            query=query_get_params,  # query
            headers={},  # header
            client_ip="127.0.0.1",
        )

        with patch.object(
            crud_related_resource,
            "_delete_many_to_many",
            new_callable=AsyncMock,
            side_effect=CollectionResourceException,
        ) as fake_delete_many_to_many:
            response = self.loop.run_until_complete(crud_related_resource.delete_list(request))
            fake_delete_many_to_many.assert_awaited()
        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()
        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "CollectionResourceException",
            "detail": "🌳🌳🌳",
            "status": 500,
        }

        # unhandled relation
        request = RequestRelationCollection(
            RequestMethod.DELETE,
            self.collection_order,
            self.collection_product,
            ManyToOne(
                {
                    "type": FieldType.MANY_TO_ONE,
                }
            ),
            "products",
            body={"data": [{"id": "201", "type": "product"}]},  # body
            query=query_get_params,  # query
            headers={},
            client_ip="127.0.0.1",
        )
        response = self.loop.run_until_complete(crud_related_resource.delete_list(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()
        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "ForestException",
            "detail": "🌳🌳🌳Unhandled relation type",
            "status": 500,
        }

    def test_delete_list_should_check_delete_permission_when_delete_flag_is_set(self):
        query_get_params = {
            "collection_name": "customer",
            "relation_name": "order",
            "timezone": "Europe/Paris",
            "fields[order]": "id,cost",
            "pks": "2",  # customer id
            "delete": True,
        }
        request = RequestRelationCollection(
            RequestMethod.DELETE,
            *self.mk_request_customer_order_one_to_many(),
            body={"data": [{"id": "201", "type": "order"}]},
            query=query_get_params,
            headers={},
            client_ip="127.0.0.1",
        )
        with patch.object(
            self.crud_related_resource, "_delete_one_to_many", new_callable=AsyncMock
        ) as fake_delete_one_to_many:
            self.loop.run_until_complete(self.crud_related_resource.delete_list(request))
            fake_delete_one_to_many.assert_awaited()
        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "delete")
        self.permission_service.can.reset_mock()

    def test_delete_list_should_check_edit_permission_when_delete_flag_is_not_set(self):
        query_get_params = {
            "collection_name": "customer",
            "relation_name": "order",
            "timezone": "Europe/Paris",
            "fields[order]": "id,cost",
            "pks": "2",  # customer id
        }
        request = RequestRelationCollection(
            RequestMethod.DELETE,
            *self.mk_request_customer_order_one_to_many(),
            body={"data": [{"id": "201", "type": "order"}]},
            query=query_get_params,
            headers={},
            client_ip="127.0.0.1",
        )
        with patch.object(
            self.crud_related_resource, "_delete_one_to_many", new_callable=AsyncMock
        ) as fake_delete_one_to_many:
            self.loop.run_until_complete(self.crud_related_resource.delete_list(request))
            fake_delete_one_to_many.assert_awaited()
        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()

    # _associate_one_to_many
    def test_associate_one_to_many(self):
        crud_related_resource = CrudRelatedResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )
        query_get_params = {
            "collection_name": "customer",
            "relation_name": "order",
            "timezone": "Europe/Paris",
            "fields[order]": "id,cost",
            "pks": "2",
        }
        request = RequestRelationCollection(
            RequestMethod.POST,
            *self.mk_request_customer_order_one_to_many(),
            query=query_get_params,
            headers={},
            client_ip="127.0.0.1",
        )

        response = self.loop.run_until_complete(crud_related_resource._associate_one_to_many(request, [201], 2))
        assert response.status == 204

        # errors
        request = RequestRelationCollection(
            RequestMethod.POST,
            self.collection_customer,
            self.collection_order,
            OneToOne(
                {
                    "type": FieldType.ONE_TO_ONE,
                    "foreign_collection": "order",
                    "origin_key": "customer_id",
                    "origin_key_target": "id",
                }
            ),
            "orders",
            query=query_get_params,
            headers={},
            client_ip="127.0.0.1",
        )
        response = self.loop.run_until_complete(crud_related_resource._associate_one_to_many(request, [201], 2))

        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "ForestException",
            "detail": "🌳🌳🌳Unhandled relation type",
            "status": 500,
        }

        request = RequestRelationCollection(
            RequestMethod.POST,
            *self.mk_request_customer_order_one_to_many(),
            query=query_get_params,
            headers={},
            client_ip="127.0.0.1",
        )
        with patch.object(self.collection_order, "update", new_callable=AsyncMock, side_effect=DatasourceException):
            response = self.loop.run_until_complete(crud_related_resource._associate_one_to_many(request, [201], 2))

        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "DatasourceException",
            "detail": "🌳🌳🌳",
            "status": 500,
        }

    # _associate_many_to_many
    def test_associate_many_to_many(self):
        crud_related_resource = CrudRelatedResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )
        query_get_params = {
            "collection_name": "order",
            "relation_name": "product",
            "timezone": "Europe/Paris",
            "pks": "2",  # order id
        }
        request = RequestRelationCollection(
            RequestMethod.POST,
            *self.mk_request_order_product_many_to_many(),
            body={"data": [{"id": "201", "type": "product"}]},  # body
            query=query_get_params,  # query
            headers={},
            client_ip="127.0.0.1",
        )
        with patch.object(
            self.collection_product_order, "create", new_callable=AsyncMock
        ) as mock_through_collection_create:
            response = self.loop.run_until_complete(crud_related_resource._associate_many_to_many(request, [201], 2))
            mock_through_collection_create.assert_awaited()
        assert response.status == 204

        request = RequestRelationCollection(
            RequestMethod.POST,
            *self.mk_request_customer_order_one_to_many(),
            body={"data": [{"id": "201", "type": "product"}]},  # body
            query=query_get_params,  # query
            headers={},
            client_ip="127.0.0.1",
        )
        response = self.loop.run_until_complete(crud_related_resource._associate_many_to_many(request, [201], 2))
        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "ForestException",
            "detail": "🌳🌳🌳Unhandled relation type",
            "status": 500,
        }

        request = RequestRelationCollection(
            RequestMethod.POST,
            *self.mk_request_order_product_many_to_many(),
            body={"data": [{"id": "201", "type": "product"}]},  # body
            query=query_get_params,  # query
            headers={},
            client_ip="127.0.0.1",
        )
        with patch.object(
            self.collection_product_order, "create", new_callable=AsyncMock, side_effect=DatasourceException
        ):
            response = self.loop.run_until_complete(crud_related_resource._associate_many_to_many(request, [201], 2))
        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "DatasourceException",
            "detail": "🌳🌳🌳",
            "status": 500,
        }

    # get_base_fk_filter
    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud_related.ConditionTreeFactory.match_ids",
        return_value=ConditionTreeLeaf("id", Operator.EQUAL, 201),
    )
    def test_get_base_fk_filter(self, mocked_match_id: Mock):
        query_get_params = {
            "collection_name": "customer",
            "relation_name": "order",
            "timezone": "Europe/Paris",
            "fields[order]": "id,cost",
            "pks": "2",  # customer id
        }
        crud_related_resource = CrudRelatedResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )
        request = RequestRelationCollection(
            RequestMethod.DELETE,
            *self.mk_request_customer_order_one_to_many(),
            body={"data": [{"id": "201", "type": "order"}]},
            query=query_get_params,
            headers={},
            client_ip="127.0.0.1",
        )

        with patch.object(
            self.permission_service,
            "get_scope",
            AsyncMock(return_value=ConditionTreeLeaf("id", Operator.GREATER_THAN, 0)),
        ):
            response = self.loop.run_until_complete(crud_related_resource.get_base_fk_filter(request))
        assert response.condition_tree.aggregator == Aggregator.AND
        assert len(response.condition_tree.conditions) == 2
        assert response.condition_tree.conditions[0].field == "id"
        assert response.condition_tree.conditions[0].operator == Operator.EQUAL
        assert response.condition_tree.conditions[0].value == 201
        assert response.condition_tree.conditions[1].field == "id"
        assert response.condition_tree.conditions[1].operator == Operator.GREATER_THAN
        assert response.condition_tree.conditions[1].value == 0

        # no id
        request = RequestRelationCollection(
            RequestMethod.DELETE,
            *self.mk_request_customer_order_one_to_many(),
            body={"data": {}},
            query=query_get_params,
            headers={},
            client_ip="127.0.0.1",
        )

        with self.assertRaises(CollectionResourceException):
            response = self.loop.run_until_complete(crud_related_resource.get_base_fk_filter(request))

        # exclude ids
        request = RequestRelationCollection(
            RequestMethod.DELETE,
            *self.mk_request_customer_order_one_to_many(),
            body={"data": {"attributes": {"all_records": True, "all_records_ids_excluded": ["201"]}}},
            query=query_get_params,
            headers={},
            client_ip="127.0.0.1",
        )
        response = self.loop.run_until_complete(crud_related_resource.get_base_fk_filter(request))

        assert response.condition_tree.aggregator == Aggregator.AND
        assert len(response.condition_tree.conditions) == 2
        assert response.condition_tree.conditions[0].field == "id"
        assert response.condition_tree.conditions[0].operator == Operator.NOT_EQUAL
        assert response.condition_tree.conditions[0].value == 201
        assert response.condition_tree.conditions[1].field == "id"
        assert response.condition_tree.conditions[1].operator == Operator.GREATER_THAN
        assert response.condition_tree.conditions[1].value == 0

    # _delete_one_to_many
    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud_related.ConditionTreeFactory.match_ids",
        return_value=ConditionTreeLeaf("id", Operator.EQUAL, "201"),
    )
    def test_delete_one_to_many(self, mocked_match_id: Mock):
        crud_related_resource = CrudRelatedResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )

        # dissociate
        query_get_params = {
            "collection_name": "customer",
            "relation_name": "order",
            "timezone": "Europe/Paris",
            "fields[order]": "id,cost",
            "pks": "2",  # customer id
        }
        request = RequestRelationCollection(
            RequestMethod.DELETE,
            *self.mk_request_customer_order_one_to_many(),
            body={"data": [{"id": "201", "type": "order"}]},
            query=query_get_params,
            headers={},
            client_ip="127.0.0.1",
        )
        _filter = self.loop.run_until_complete(crud_related_resource.get_base_fk_filter(request))

        self.loop.run_until_complete(crud_related_resource._delete_one_to_many(request, [2], False, _filter))
        self.collection_order.update.assert_awaited()

        # remove
        query_get_params["delete"] = True
        request = RequestRelationCollection(
            "DELETE",
            *self.mk_request_customer_order_one_to_many(),
            body={"data": [{"id": "201", "type": "order"}]},
            query=query_get_params,
            headers={},
            client_ip="127.0.0.1",
        )
        _filter = self.loop.run_until_complete(crud_related_resource.get_base_fk_filter(request))

        self.loop.run_until_complete(crud_related_resource._delete_one_to_many(request, [2], True, _filter))
        self.collection_order.delete.assert_awaited()

        # error
        request = RequestRelationCollection(
            RequestMethod.DELETE,
            *self.mk_request_order_product_many_to_many(),
            body={"data": [{"id": "201", "type": "product"}]},  # body
            query=query_get_params,  # query
            headers={},
            client_ip="127.0.0.1",
        )

        _filter = self.loop.run_until_complete(crud_related_resource.get_base_fk_filter(request))

        self.assertRaises(
            CollectionResourceException,
            self.loop.run_until_complete,
            crud_related_resource._delete_one_to_many(request, [2], True, _filter),
        )

    # _delete_many_to_many
    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud_related.ConditionTreeFactory.match_ids",
        return_value=ConditionTreeLeaf("id", Operator.EQUAL, 201),
    )
    def test_delete_many_to_many(self, mocked_match_id: Mock):
        crud_related_resource = CrudRelatedResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )
        # dissociate
        query_get_params = {
            "collection_name": "product",
            "relation_name": "order",
            "timezone": "Europe/Paris",
            "pks": "2",
            "delete": "false",
        }
        request = RequestRelationCollection(
            RequestMethod.DELETE,
            *self.mk_request_order_product_many_to_many(),
            body={"data": [{"id": "201", "type": "product"}]},  # body
            query=query_get_params,  # query
            headers={},
            client_ip="127.0.0.1",
        )
        _filter = self.loop.run_until_complete(crud_related_resource.get_base_fk_filter(request))

        with patch.object(self.collection_product, "list", new_callable=AsyncMock, return_value=[{"id": 1}, {"id": 2}]):
            with patch.object(
                self.collection_product_order,
                "list",
                new_callable=AsyncMock,
                return_value=[{"product_id": 1}, {"product_id": 2}],
            ):
                self.loop.run_until_complete(crud_related_resource._delete_many_to_many(request, [2], False, _filter))
        self.datasource.get_collection("product_order").delete.assert_awaited()

        # delete
        query_get_params["delete"] = "true"
        request = RequestRelationCollection(
            RequestMethod.DELETE,
            *self.mk_request_order_product_many_to_many(),
            body={"data": [{"id": "201", "type": "product"}]},  # body
            query=query_get_params,  # query
            headers={},
            client_ip="127.0.0.1",
        )

        _filter = self.loop.run_until_complete(crud_related_resource.get_base_fk_filter(request))

        with patch.object(self.collection_product_order, "list", new_callable=AsyncMock):
            with patch.object(
                self.collection_product,
                "list",
                new_callable=AsyncMock,
                return_value=[{"id": 1}, {"id": 2}],
            ):
                self.loop.run_until_complete(crud_related_resource._delete_many_to_many(request, [2], True, _filter))
        self.collection_product.delete.assert_awaited()

        # errors
        request = RequestRelationCollection(
            RequestMethod.DELETE,
            *self.mk_request_customer_order_one_to_many(),
            body={"data": [{"id": 201, "type": "order"}]},
            query=query_get_params,
            headers={},
            client_ip="127.0.0.1",
        )

        self.assertRaises(
            CollectionResourceException,
            self.loop.run_until_complete,
            crud_related_resource._delete_many_to_many(request, [2], True, _filter),
        )

        request = RequestRelationCollection(
            RequestMethod.DELETE,
            *self.mk_request_order_product_many_to_many(),
            body={"data": [{"id": "201", "type": "product"}]},  # body
            query=query_get_params,  # query
            headers={},
            client_ip="127.0.0.1",
        )
        with patch.object(self.collection_product, "delete", side_effect=DatasourceException, new_callable=AsyncMock):
            with patch.object(self.collection_product_order, "list", new_callable=AsyncMock):
                with patch.object(
                    self.collection_product,
                    "list",
                    new_callable=AsyncMock,
                    return_value=[{"id": 1}, {"id": 2}],
                ):
                    self.loop.run_until_complete(
                        crud_related_resource._delete_many_to_many(request, [2], True, _filter)
                    )

    # _update_one_to_one
    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud_related.ConditionTreeFactory.match_ids",
        return_value=ConditionTreeLeaf("id", Operator.EQUAL, 201),
    )
    def test_update_one_to_one(self, mock_match_ids: Mock):
        crud_related_resource = CrudRelatedResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )

        query_get_params = {
            "collection_name": "order",
            "relation_name": "cart",
            "timezone": "Europe/Paris",
            "pks": "2",  # order id
        }
        request = RequestRelationCollection(
            RequestMethod.PUT,
            self.collection_order,
            self.collection_cart,
            OneToOne(
                {
                    "type": FieldType.ONE_TO_ONE,
                    "foreign_collection": "cart",
                    "origin_key": "order_id",
                    "origin_key_target": "id",
                }
            ),
            "orders",
            body={"data": {"id": "201", "type": "cart"}},  # body
            query=query_get_params,  # query
            headers={},
            client_ip="127.0.0.1",
        )

        self.loop.run_until_complete(
            crud_related_resource._update_one_to_one(request, [2], [201], zoneinfo.ZoneInfo("Europe/Paris"))
        )
        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "edit")
        self.permission_service.can.reset_mock()
        # self.collection_order.update.assert_awaited()
        self.collection_cart.update.assert_awaited()
        update_call_list = self.collection_cart.update.await_args_list
        first_call_filter = update_call_list[0][0][1].condition_tree
        assert first_call_filter.conditions[0].field == "order_id"
        assert first_call_filter.conditions[0].operator == Operator.EQUAL
        assert first_call_filter.conditions[0].value == 2

        assert first_call_filter.conditions[1].field == "id"
        assert first_call_filter.conditions[1].operator == Operator.GREATER_THAN
        assert first_call_filter.conditions[1].value == 0

        first_call_patch = update_call_list[0][0][2]
        assert "order_id" in first_call_patch
        # assert first_call_patch["order_id"] is None

        second_call_filter = update_call_list[1][0][1].condition_tree
        assert second_call_filter.conditions[0].field == "id"
        assert second_call_filter.conditions[0].operator == Operator.EQUAL
        assert second_call_filter.conditions[0].value == 201

        assert second_call_filter.conditions[1].field == "id"
        assert second_call_filter.conditions[1].operator == Operator.GREATER_THAN
        assert second_call_filter.conditions[1].value == 0

        second_call_patch = update_call_list[1][0][2]
        assert second_call_patch["order_id"] == 2

        # error
        request = RequestRelationCollection(
            RequestMethod.PUT,
            self.collection_order,
            self.collection_cart,
            ManyToMany(  # error
                {
                    "type": FieldType.MANY_TO_MANY,
                    "foreign_collection": "cart",
                    "origin_key": "order_id",
                    "origin_key_target": "id",
                }
            ),
            "orders",
            body={"data": {"id": "201", "type": "cart"}},  # body
            query=query_get_params,  # query
            headers={},
            client_ip="127.0.0.1",
        )

        self.assertRaises(
            CollectionResourceException,
            self.loop.run_until_complete,
            crud_related_resource._update_one_to_one(request, [2], [201], zoneinfo.ZoneInfo("Europe/Paris")),
        )
        self.permission_service.can.assert_not_awaited()
        self.permission_service.can.reset_mock()

    def test_update_one_to_one_should_not_call_update_a_second_time_if_value_is_null(self):
        crud_related_resource = CrudRelatedResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )

        query_get_params = {
            "collection_name": "order",
            "relation_name": "cart",
            "timezone": "Europe/Paris",
            "pks": "2",  # order id
        }
        request = RequestRelationCollection(
            RequestMethod.PUT,
            self.collection_order,
            self.collection_cart,
            OneToOne(
                {
                    "type": FieldType.ONE_TO_ONE,
                    "foreign_collection": "cart",
                    "origin_key": "order_id",
                    "origin_key_target": "id",
                }
            ),
            "orders",
            body={"data": None},  # body
            query=query_get_params,  # query
            headers={},
            client_ip="127.0.0.1",
        )

        with patch.object(self.collection_cart, "update", new_callable=AsyncMock) as mock_update:
            self.loop.run_until_complete(
                crud_related_resource._update_one_to_one(request, [2], None, zoneinfo.ZoneInfo("Europe/Paris"))
            )
            self.assertIn(
                ConditionTreeLeaf("order_id", "equal", 2), mock_update.await_args.args[1].condition_tree.conditions
            )
            self.assertEqual(mock_update.await_args.args[2], {"order_id": None})

            self.assertEqual(mock_update.await_count, 1)

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud_related.ConditionTreeFactory.match_ids",
        return_value=ConditionTreeLeaf("id", Operator.EQUAL, 201),
    )
    def test_update_many_to_one(self, mock_match_ids: Mock):
        crud_related_resource = CrudRelatedResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )

        query_get_params = {
            "collection_name": "order",
            "relation_name": "customer",
            "timezone": "Europe/Paris",
            "pks": "2",  # order id
        }
        request = RequestRelationCollection(
            RequestMethod.PUT,
            self.collection_order,
            self.collection_customer,
            ManyToOne(
                type=FieldType.MANY_TO_ONE,
                foreign_collection="customer",
                foreign_key="customer_id",
                foreign_key_target="id",
            ),
            "relation_name",
            body={"data": {"id": "201", "type": "customer"}},
            query=query_get_params,  # query
            headers={},
            client_ip="127.0.0.1",
        )

        self.collection_order.update.reset_mock()
        self.loop.run_until_complete(
            crud_related_resource._update_many_to_one(request, [2], [201], zoneinfo.ZoneInfo("Europe/Paris"))
        )
        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()
        self.collection_order.update.assert_awaited_once_with(ANY, ANY, {"customer_id": 201})

        # error
        request = RequestRelationCollection(
            RequestMethod.PUT,
            self.collection_order,
            self.collection_customer,
            ManyToMany(  # error
                type=FieldType.MANY_TO_MANY,
                foreign_collection="customer",
                foreign_key="customer_id",
                foreign_key_target="id",
            ),
            "relation_name",
            body={"data": {"id": "201", "type": "customer"}},
            query=query_get_params,  # query
            headers={},
            client_ip="127.0.0.1",
        )

        self.assertRaises(
            CollectionResourceException,
            self.loop.run_until_complete,
            crud_related_resource._update_many_to_one(request, [2], [201], zoneinfo.ZoneInfo("Europe/Paris")),
        )

        self.permission_service.can.assert_not_awaited()
