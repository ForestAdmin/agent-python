import asyncio
import csv
import importlib
import json
import sys
from io import StringIO
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
from forestadmin.agent_toolkit.services.serializers.json_api import JsonApiException
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
                    "filter_operators": set([Operator.PRESENT]),
                },
                "cost": {"column_type": PrimitiveType.NUMBER, "is_primary_key": False, "type": FieldType.COLUMN},
                "products": {
                    "column_type": PrimitiveType.NUMBER,
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
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": False,
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
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": False,
                    "type": FieldType.ONE_TO_ONE,
                    "foreign_collection": "cart",
                    "origin_key_target": "id",
                    "origin_key": "order_id",
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
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": False,
                    "type": FieldType.ONE_TO_MANY,
                    "foreign_collection": "order",
                    "origin_key": "customer_id",
                    "origin_key_target": "id",
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
            method="GET",
            query={"collection_name": "customer", "relation_name": "order"},
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
            method="GET",
            query={"collection_name": "customer", "relation_name": "order"},
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
    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud_related.JsonApiSerializer.get",
        return_value=Mock,
    )
    def test_list(self, mocked_json_serializer_get: Mock):
        mock_orders = [{"id": 10, "cost": 200}, {"id": 11, "cost": 201}]

        request = RequestRelationCollection(
            RequestMethod.GET,
            *self.mk_request_customer_order_one_to_many(),
            None,
            {
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
                "pks": "2",  # customer id
                "search_extended": 0,
                "search": "20",
            },
            {},
            None,
        )
        crud_related_resource = CrudRelatedResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )

        mocked_json_serializer_get.return_value.dump = Mock(
            return_value={
                "data": [
                    {"type": "order", "attributes": mock_order, "id": mock_order["id"]} for mock_order in mock_orders
                ]
            }
        )

        with patch.object(
            self.collection_order, "list", new_callable=AsyncMock, return_value=mock_orders
        ) as mocked_collection_list:
            response = self.loop.run_until_complete(crud_related_resource.list(request))
            mocked_collection_list.assert_awaited()

        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "browse")
        self.permission_service.can.reset_mock()

        assert response.status == 200
        response_content = json.loads(response.body)
        assert isinstance(response_content["data"], list)
        assert len(response_content["data"]) == 2
        assert response_content["data"][0]["attributes"]["cost"] == mock_orders[0]["cost"]
        assert response_content["data"][0]["id"] == mock_orders[0]["id"]
        assert response_content["data"][0]["type"] == "order"
        assert response_content["data"][1]["attributes"]["cost"] == mock_orders[1]["cost"]
        assert response_content["data"][1]["id"] == mock_orders[1]["id"]
        assert response_content["data"][1]["type"] == "order"

        assert response_content["meta"]["decorators"]["0"] == {"id": 10, "search": ["cost"]}
        assert response_content["meta"]["decorators"]["1"] == {"id": 11, "search": ["cost"]}

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud_related.JsonApiSerializer.get",
        return_value=Mock,
    )
    def test_list_errors(self, mocked_json_serializer_get: Mock):
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
        )

        response = self.loop.run_until_complete(crud_related_resource.list(request))

        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "browse")
        self.permission_service.can.reset_mock()

        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "ForestException",
            "detail": "🌳🌳🌳Unhandled relation type",
            "status": 500,
        }

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
            None,
            request_get_params,
            {},
            None,
        )

        response = self.loop.run_until_complete(crud_related_resource.list(request))

        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "browse")
        self.permission_service.can.reset_mock()

        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "CollectionResourceException",
            "detail": "🌳🌳🌳primary keys are missing",
            "status": 500,
        }

        # # JsonApiException
        request_get_params["pks"] = "2"
        request = RequestRelationCollection(
            RequestMethod.GET,
            *self.mk_request_customer_order_one_to_many(),
            None,
            request_get_params,
            {},
            None,
        )
        self.collection_order.list = AsyncMock(return_value=mock_orders)
        mocked_json_serializer_get.return_value.dump = Mock(side_effect=JsonApiException)

        response = self.loop.run_until_complete(crud_related_resource.list(request))

        self.permission_service.can.assert_any_await(request.user, request.foreign_collection, "browse")
        self.permission_service.can.reset_mock()

        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "JsonApiException",
            "detail": "🌳🌳🌳",
            "status": 500,
        }

    # CSV
    def test_csv(self):
        mock_orders = [{"id": 10, "cost": 200}, {"id": 11, "cost": 201}]

        request = RequestRelationCollection(
            RequestMethod.GET,
            *self.mk_request_customer_order_one_to_many(),
            None,
            {
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
                "pks": "2",  # customer id
                "search_extended": 0,
                "search": "20",
            },
            {},
            None,
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
        csv_reader = csv.DictReader(StringIO(response.body))
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
            None,
            request_get_params,
            {},
            None,
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
            None,
            request_get_params,
            {},
            None,
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
            None,
            {
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
                "pks": "2",  # customer id
                "search_extended": 0,
                "search": "20",
            },
            {},
            None,
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
            {"data": [{"id": "201", "type": "order"}]},  # body
            {
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "pks": "2",  # customer id
            },  # query
            {},  # header
            None,  # user
        )
        crud_related_resource = CrudRelatedResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )

        with patch.object(self.collection_order, "update", new_callable=AsyncMock) as mock_collection_update:
            response = self.loop.run_until_complete(crud_related_resource.add(request))
            mock_collection_update.assert_awaited()

        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()
        assert response.status == 204

        # many to Many
        request = RequestRelationCollection(
            RequestMethod.POST,
            *self.mk_request_order_product_many_to_many(),
            {"data": [{"id": "201", "type": "product"}]},  # body
            {
                "collection_name": "order",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "pks": "2",  # order id
            },  # query
            {},  # header
            None,  # user
        )
        crud_related_resource = CrudRelatedResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )

        with patch.object(self.collection_product_order, "create", new_callable=AsyncMock) as mock_collection_create:
            response = self.loop.run_until_complete(crud_related_resource.add(request))

            mock_collection_create.assert_awaited()
        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()

        assert response.status == 204

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud_related.JsonApiSerializer.get",
        return_value=Mock,
    )
    def test_add_errors(
        self,
        mocked_json_serializer_get: Mock,
    ):
        request_get_params = {
            "collection_name": "customer",
            "relation_name": "order",
            "timezone": "Europe/Paris",
            # "pks": "2",  # customer id
        }
        request = RequestRelationCollection(
            RequestMethod.POST,
            *self.mk_request_customer_order_one_to_many(),
            {"data": [{"id": "201", "type": "order"}]},  # body
            request_get_params,  # query
            {},  # header
            None,  # user
        )

        # no_id exception
        response = self.loop.run_until_complete(self.crud_related_resource.add(request))

        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()

        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "CollectionResourceException",
            "detail": "🌳🌳🌳primary keys are missing",
            "status": 500,
        }
        # no date body id
        request_get_params["pks"] = "2"
        request = RequestRelationCollection(
            RequestMethod.POST,
            *self.mk_request_customer_order_one_to_many(),
            {},  # body
            request_get_params,  # query
            {},  # header
            None,  # user
        )
        response = self.loop.run_until_complete(self.crud_related_resource.add(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()
        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "ForestException",
            "detail": "🌳🌳🌳missing target's id",
            "status": 500,
        }

        # unpack foreign id
        request = RequestRelationCollection(
            RequestMethod.POST,
            *self.mk_request_customer_order_one_to_many(),
            {"data": [{"id": "201", "type": "order"}]},  # body
            request_get_params,  # query
            {},  # header
            None,  # user
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

        # Unhandled relation type
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
            {"data": [{"id": "201", "type": "order"}]},  # body
            request_get_params,  # query
            {},  # header
            None,  # user
        )
        response = self.loop.run_until_complete(self.crud_related_resource.add(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()
        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "ForestException",
            "detail": "🌳🌳🌳Unhandled relation type",
            "status": 500,
        }

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
            {"data": {"id": "201", "type": "cart"}},  # body
            {
                "collection_name": "order",
                "relation_name": "cart",
                "timezone": "Europe/Paris",
                "pks": "2",  # order id
            },  # query
            {},  # header
            None,  # user
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
            {"data": {"id": "201", "type": "customer"}},  # body
            {
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "pks": "2",  # customer id
            },  # query
            {},  # header
            None,  # user
        )

        response = self.loop.run_until_complete(crud_related_resource.update_list(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()

        assert response.status == 204
        self.collection_cart.update.assert_awaited()

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
            {"data": {"id": "201", "type": "customer"}},  # body
            query_get_params,  # query
            {},  # header
            None,  # user
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
        # no id for relation
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
            {"data": {"__id": "201", "type": "customer"}},  # body
            query_get_params,  # query
            {},  # header
            None,  # user
        )
        response = self.loop.run_until_complete(crud_related_resource.update_list(request))
        self.permission_service.can.assert_not_awaited()

        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "ForestException",
            "detail": "🌳🌳🌳Relation id is missing",
            "status": 500,
        }

        # unpack_id raises Exception
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
            {"data": {"id": "201", "type": "customer"}},  # body
            query_get_params,  # query
            {},  # header
            None,  # user
        )

        def mocked_unpack_id(schema, pk):
            if pk != "201":
                return unpack_id(schema, pk)
            else:
                raise CollectionResourceException()

        with patch("forestadmin.agent_toolkit.resources.collections.crud_related.unpack_id", mocked_unpack_id):
            response = self.loop.run_until_complete(crud_related_resource.update_list(request))
        self.permission_service.can.assert_not_awaited()

        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "CollectionResourceException",
            "detail": "🌳🌳🌳",
            "status": 500,
        }

        # Error in update relation
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
            {"data": {"id": "201", "type": "customer"}},  # body
            query_get_params,  # query
            {},  # header
            None,  # user
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
            {"data": {"id": "201", "type": "customer"}},  # body
            query_get_params,  # query
            {},  # header
            None,  # user
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
            None,
            {
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
                "pks": "2",  # customer id
            },
            {},
            None,
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
            None,
            {
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
                "pks": "2",  # customer id
            },
            {},
            None,
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
            None,
            query_get_params,
            {},
            None,
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
            None,
            query_get_params,
            {},
            None,
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
            {"data": [{"id": "201", "type": "order"}]},
            query_get_params,
            {},
            None,
        )
        with patch.object(
            self.crud_related_resource, "_delete_one_to_many", new_callable=AsyncMock
        ) as fake_delete_one_to_many:
            response = self.loop.run_until_complete(self.crud_related_resource.delete_list(request))
            fake_delete_one_to_many.assert_awaited()
        self.permission_service.can.assert_any_await(request.user, request.collection, "delete")
        self.permission_service.can.reset_mock()

        assert response.status == 204

        # remove many_to_many
        # many to many (order & products)
        del query_get_params["fields[order]"]
        request = RequestRelationCollection(
            RequestMethod.DELETE,
            *self.mk_request_order_product_many_to_many(),
            {"data": [{"id": "201", "type": "product"}]},  # body
            query_get_params,  # query
            {},  # header
            None,  # user
        )
        with patch.object(
            self.crud_related_resource, "_delete_many_to_many", new_callable=AsyncMock
        ) as fake_delete_many_to_many:
            response = self.loop.run_until_complete(self.crud_related_resource.delete_list(request))
            fake_delete_many_to_many.assert_awaited()
        self.permission_service.can.assert_any_await(request.user, request.collection, "delete")
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
            {"data": [{"id": "201", "type": "product"}]},  # body
            query_get_params,  # query
            {},  # header
            None,  # user
        )
        response = self.loop.run_until_complete(crud_related_resource.delete_list(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "delete")
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
            {"data": [{"id": "201", "type": "product"}]},  # body
            query_get_params,  # query
            {},  # header
            None,  # user
        )

        with patch.object(
            crud_related_resource,
            "_delete_many_to_many",
            new_callable=AsyncMock,
            side_effect=CollectionResourceException,
        ) as fake_delete_many_to_many:
            response = self.loop.run_until_complete(crud_related_resource.delete_list(request))
            fake_delete_many_to_many.assert_awaited()
        self.permission_service.can.assert_any_await(request.user, request.collection, "delete")
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
            {"data": [{"id": "201", "type": "product"}]},  # body
            query_get_params,  # query
            {},  # header
            None,  # user
        )
        response = self.loop.run_until_complete(crud_related_resource.delete_list(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "delete")
        self.permission_service.can.reset_mock()
        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "ForestException",
            "detail": "🌳🌳🌳Unhandled relation type",
            "status": 500,
        }

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
            None,
            query_get_params,
            {},
            None,
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
            None,
            query_get_params,
            {},
            None,
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
            None,
            query_get_params,
            {},
            None,
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
            {"data": [{"id": "201", "type": "product"}]},  # body
            query_get_params,  # query
            {},  # header
            None,  # user
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
            {"data": [{"id": "201", "type": "product"}]},  # body
            query_get_params,  # query
            {},  # header
            None,  # user
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
            {"data": [{"id": "201", "type": "product"}]},  # body
            query_get_params,  # query
            {},  # header
            None,  # user
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
            {"data": [{"id": "201", "type": "order"}]},
            query_get_params,
            {},
            None,
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
            {"data": {}},
            query_get_params,
            {},
            None,
        )

        with self.assertRaises(CollectionResourceException):
            response = self.loop.run_until_complete(crud_related_resource.get_base_fk_filter(request))

        # exclude ids
        request = RequestRelationCollection(
            RequestMethod.DELETE,
            *self.mk_request_customer_order_one_to_many(),
            {"data": {"attributes": {"all_records": True, "all_records_ids_excluded": ["201"]}}},
            query_get_params,
            {},
            None,
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
            {"data": [{"id": "201", "type": "order"}]},
            query_get_params,
            {},
            None,
        )
        _filter = self.loop.run_until_complete(crud_related_resource.get_base_fk_filter(request))

        self.loop.run_until_complete(crud_related_resource._delete_one_to_many(request, [2], False, _filter))
        self.collection_order.update.assert_awaited()

        # remove
        query_get_params["delete"] = True
        request = RequestRelationCollection(
            "DELETE",
            *self.mk_request_customer_order_one_to_many(),
            {"data": [{"id": "201", "type": "order"}]},
            query_get_params,
            {},
            None,
        )
        _filter = self.loop.run_until_complete(crud_related_resource.get_base_fk_filter(request))

        self.loop.run_until_complete(crud_related_resource._delete_one_to_many(request, [2], True, _filter))
        self.collection_order.delete.assert_awaited()

        # error
        request = RequestRelationCollection(
            RequestMethod.DELETE,
            *self.mk_request_order_product_many_to_many(),
            {"data": [{"id": "201", "type": "product"}]},  # body
            query_get_params,  # query
            {},  # header
            None,  # user
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
            {"data": [{"id": "201", "type": "product"}]},  # body
            query_get_params,  # query
            {},  # header
            None,  # user
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
            {"data": [{"id": "201", "type": "product"}]},  # body
            query_get_params,  # query
            {},  # header
            None,  # user
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
            {"data": [{"id": 201, "type": "order"}]},
            query_get_params,
            {},
            None,
        )

        self.assertRaises(
            CollectionResourceException,
            self.loop.run_until_complete,
            crud_related_resource._delete_many_to_many(request, [2], True, _filter),
        )

        request = RequestRelationCollection(
            RequestMethod.DELETE,
            *self.mk_request_order_product_many_to_many(),
            {"data": [{"id": "201", "type": "product"}]},  # body
            query_get_params,  # query
            {},  # header
            None,  # user
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
            {"data": {"id": "201", "type": "cart"}},  # body
            query_get_params,  # query
            {},  # header
            None,  # user
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
            {"data": {"id": "201", "type": "cart"}},  # body
            query_get_params,  # query
            {},  # header
            None,  # user
        )

        self.assertRaises(
            CollectionResourceException,
            self.loop.run_until_complete,
            crud_related_resource._update_one_to_one(request, [2], [201], zoneinfo.ZoneInfo("Europe/Paris")),
        )
        self.permission_service.can.assert_not_awaited()
        self.permission_service.can.reset_mock()

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
            {"data": {"id": "201", "type": "customer"}},
            query_get_params,  # query
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
            {"data": {"id": "201", "type": "customer"}},
            query_get_params,  # query
        )

        self.assertRaises(
            CollectionResourceException,
            self.loop.run_until_complete,
            crud_related_resource._update_many_to_one(request, [2], [201], zoneinfo.ZoneInfo("Europe/Paris")),
        )

        self.permission_service.can.assert_not_awaited()
