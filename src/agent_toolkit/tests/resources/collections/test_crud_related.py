import asyncio
import csv
import importlib
import json
import sys
from unittest import TestCase
from unittest.mock import Mock, patch

from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import Aggregator

if sys.version_info < (3, 8):
    from mock import AsyncMock
else:
    from unittest.mock import AsyncMock

import forestadmin.agent_toolkit.resources.collections.crud_related
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.resources.collections.exceptions import CollectionResourceException
from forestadmin.agent_toolkit.resources.collections.requests import (
    RequestCollectionException,
    RequestRelationCollection,
)
from forestadmin.agent_toolkit.services.permissions import PermissionService
from forestadmin.agent_toolkit.services.serializers.json_api import JsonApiException
from forestadmin.agent_toolkit.utils.context import Request
from forestadmin.agent_toolkit.utils.csv import CsvException
from forestadmin.agent_toolkit.utils.id import unpack_id
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource, DatasourceException
from forestadmin.datasource_toolkit.interfaces.fields import (
    FieldType,
    ManyToMany,
    ManyToOne,
    OneToMany,
    Operator,
    PrimitiveType,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf


def mock_decorator_with_param(*args, **kwargs):
    def decorator(fn):
        def decorated_function(*args, **kwargs):
            return fn(*args, **kwargs)

        return decorated_function

    return decorator


def mock_decorator_no_param(fn):
    def decorated_function(*args, **kwargs):
        return fn(*args, **kwargs)

    return decorated_function


patch("forestadmin.agent_toolkit.resources.collections.decorators.check_method", mock_decorator_with_param).start()
patch("forestadmin.agent_toolkit.resources.collections.decorators.authenticate", mock_decorator_no_param).start()
patch("forestadmin.agent_toolkit.resources.collections.decorators.authorize", mock_decorator_with_param).start()

importlib.reload(forestadmin.agent_toolkit.resources.collections.crud_related)
from forestadmin.agent_toolkit.resources.collections.crud_related import CrudRelatedResource  # noqa: E402


class TestCrudRelatedResource(TestCase):
    @classmethod
    def _create_collections(cls):
        # order
        cls.collection_order = Mock(Collection)
        cls.collection_order._datasource = cls.datasource
        cls.collection_order.datasource = cls.datasource
        cls.collection_order.update = AsyncMock(return_value=None)
        cls.collection_order._name = "order"
        cls.collection_order.name = "order"
        cls.collection_order.get_field = lambda x: cls.collection_order._schema["fields"][x]
        cls.collection_order._schema = {
            "actions": {},
            "fields": {
                "id": {"column_type": PrimitiveType.NUMBER, "is_primary_key": True, "type": FieldType.COLUMN},
                "cost": {"column_type": PrimitiveType.NUMBER, "is_primary_key": False, "type": FieldType.COLUMN},
                "products": {
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": False,
                    "type": FieldType.MANY_TO_MANY,
                },
                "customer": {
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": False,
                    "type": FieldType.MANY_TO_ONE,
                    "foreign_collection": "customer",
                    "foreign_key_target": "id",
                    "foreign_key": "customer",
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
            "searchable": True,
            "segments": [],
        }
        cls.collection_order.schema = cls.collection_order._schema

        # product order
        cls.collection_product_order = Mock(Collection)
        cls.collection_product_order._datasource = cls.datasource
        cls.collection_product_order.datasource = cls.datasource
        cls.collection_product_order.update = AsyncMock(return_value=None)
        cls.collection_product_order._name = "product_order"
        cls.collection_product_order.name = "product_order"
        cls.collection_product_order.get_field = lambda x: cls.collection_product_order._schema["fields"][x]
        cls.collection_product_order._schema = {
            "actions": {},
            "fields": {
                "product_id": {"column_type": PrimitiveType.NUMBER, "is_primary_key": True, "type": FieldType.COLUMN},
                "order_id": {"column_type": PrimitiveType.NUMBER, "is_primary_key": True, "type": FieldType.COLUMN},
                "searchable": True,
                "segments": [],
            },
        }
        cls.collection_product_order.schema = cls.collection_product_order._schema

        # product

        cls.collection_product = Mock(Collection)
        cls.collection_product._datasource = cls.datasource
        cls.collection_product.datasource = cls.datasource
        cls.collection_product.update = AsyncMock(return_value=None)
        cls.collection_product._name = "product"
        cls.collection_product.name = "product"
        cls.collection_product.get_field = lambda x: cls.collection_product._schema["fields"][x]
        cls.collection_product._schema = {
            "actions": {},
            "fields": {
                "id": {"column_type": PrimitiveType.NUMBER, "is_primary_key": True, "type": FieldType.COLUMN},
                "name": {"column_type": PrimitiveType.STRING, "is_primary_key": False, "type": FieldType.COLUMN},
            },
            "searchable": False,
            "segments": [],
        }
        cls.collection_product.schema = cls.collection_product._schema

        # status

        # cls.collection_status = Mock(Collection)
        # cls.collection_status._datasource = cls.datasource
        # cls.collection_status.datasource = cls.datasource
        # cls.collection_status.update = AsyncMock(return_value=None)
        # cls.collection_status._name = "status"
        # cls.collection_status.name = "status"
        # cls.collection_status.get_field = lambda x: cls.collection_status._schema["fields"][x]
        # cls.collection_status._schema = {
        #     "actions": {},
        #     "fields": {
        #         "id": {"column_type": PrimitiveType.NUMBER, "is_primary_key": True, "type": FieldType.COLUMN},
        #         "name": {"column_type": PrimitiveType.STRING, "is_primary_key": False, "type": FieldType.COLUMN},
        #     },
        #     "searchable": False,
        #     "segments": [],
        # }
        # cls.collection_status.schema = cls.collection_status._schema

        # cart
        cls.collection_cart = Mock(Collection)
        cls.collection_cart._datasource = cls.datasource
        cls.collection_cart.datasource = cls.datasource
        cls.collection_cart.update = AsyncMock(return_value=None)
        cls.collection_cart._name = "cart"
        cls.collection_cart.name = "cart"
        cls.collection_cart.get_field = lambda x: cls.collection_cart._schema["fields"][x]
        cls.collection_cart._schema = {
            "actions": {},
            "fields": {
                "id": {"column_type": PrimitiveType.NUMBER, "is_primary_key": True, "type": FieldType.COLUMN},
                "name": {"column_type": PrimitiveType.STRING, "is_primary_key": False, "type": FieldType.COLUMN},
            },
            "searchable": False,
            "segments": [],
        }
        cls.collection_cart.schema = cls.collection_cart._schema

        # customers

        cls.collection_customer = Mock(Collection)
        cls.collection_customer._datasource = cls.datasource
        cls.collection_customer.datasource = cls.datasource
        cls.collection_customer.update = AsyncMock(return_value=None)
        cls.collection_customer._name = "customer"
        cls.collection_customer.name = "customer"
        cls.collection_customer.get_field = lambda x: cls.collection_customer._schema["fields"][x]
        cls.collection_customer._schema = {
            "actions": {},
            "fields": {
                "id": {"column_type": PrimitiveType.NUMBER, "is_primary_key": True, "type": FieldType.COLUMN},
                "name": {"column_type": PrimitiveType.STRING, "is_primary_key": False, "type": FieldType.COLUMN},
                "order": {
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": False,
                    "type": FieldType.MANY_TO_MANY,
                    "foreign_collection": "order",
                    "origin_key_target": "id",
                    # "origin_key": "_id",
                },
            },
            "searchable": False,
            "segments": [],
        }
        cls.collection_customer.schema = cls.collection_customer._schema

    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.permission_service = Mock(PermissionService)
        cls.permission_service.get_scope = AsyncMock(return_value=ConditionTreeLeaf("id", Operator.GREATER_THAN, 0))
        cls.permission_service.can = AsyncMock()
        cls.options = Options(
            auth_secret="fake_secret",
            env_secret="fake_secret",
            server_url="http://fake:5000",
            prefix="forest",
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

    # dispatch

    def test_dispatch(self):
        request = Request(
            method="GET",
            query={"collection_name": "customer", "relation_name": "order"},
        )
        crud_related_resource = CrudRelatedResource(self.datasource, self.permission_service, self.options)
        crud_related_resource.list = AsyncMock()
        crud_related_resource.csv = AsyncMock()
        crud_related_resource.count = AsyncMock()
        crud_related_resource.add = AsyncMock()
        crud_related_resource.update_list = AsyncMock()
        crud_related_resource.delete_list = AsyncMock()

        self.loop.run_until_complete(crud_related_resource.dispatch(request, "list"))
        crud_related_resource.list.assert_called_once()

        self.loop.run_until_complete(crud_related_resource.dispatch(request, "count"))
        crud_related_resource.count.assert_called_once()

        self.loop.run_until_complete(crud_related_resource.dispatch(request, "add"))
        crud_related_resource.add.assert_called_once()

        self.loop.run_until_complete(crud_related_resource.dispatch(request, "update_list"))
        crud_related_resource.update_list.assert_called_once()

        self.loop.run_until_complete(crud_related_resource.dispatch(request, "delete_list"))
        crud_related_resource.delete_list.assert_called_once()

        self.loop.run_until_complete(crud_related_resource.dispatch(request, "csv"))
        crud_related_resource.csv.assert_called_once()

    @patch("forestadmin.agent_toolkit.resources.collections.crud_related.RequestRelationCollection")
    def test_dispatch_error(self, mock_request_relation_collection: Mock):
        request = Request(
            method="GET",
            query={"collection_name": "customer", "relation_name": "order"},
        )
        mock_request_relation_collection.from_request = Mock(side_effect=RequestCollectionException("test exception"))
        crud_related_resource = CrudRelatedResource(self.datasource, self.permission_service, self.options)
        crud_related_resource.get = AsyncMock()

        response = self.loop.run_until_complete(crud_related_resource.dispatch(request, "get"))
        assert json.loads(response.body)["errors"][0] == "🌳🌳🌳test exception"
        assert response.status == 400

    # list

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud_related.JsonApiSerializer.get",
        return_value=Mock,
    )
    def test_list(self, mocked_json_serializer_get: Mock):
        mock_orders = [{"id": 10, "cost": 200}, {"id": 11, "cost": 201}]

        request = RequestRelationCollection(
            "GET",
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
            "orders",
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
        crud_related_resource = CrudRelatedResource(self.datasource, self.permission_service, self.options)

        mocked_json_serializer_get.return_value.dump = Mock(
            return_value={
                "data": [
                    {"type": "order", "attributes": mock_order, "id": mock_order["id"]} for mock_order in mock_orders
                ]
            }
        )
        self.collection_order.list = AsyncMock(return_value=mock_orders)

        response = self.loop.run_until_complete(crud_related_resource.list(request))

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
        self.collection_order.list.assert_awaited()

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud_related.JsonApiSerializer.get",
        return_value=Mock,
    )
    def test_list_errors(self, mocked_json_serializer_get: Mock):
        mock_orders = [{"id": 10, "cost": 200}, {"id": 11, "cost": 201}]
        crud_related_resource = CrudRelatedResource(self.datasource, self.permission_service, self.options)

        # Relation Type
        request = RequestRelationCollection(
            "GET",
            self.collection_customer,
            self.collection_order,
            OneToMany(
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

        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳Unhandled relation type"

        # collectionResourceException
        request = RequestRelationCollection(
            "GET",
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
            "orders",
            None,
            {
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
                # "pks": "2",  # error on customer id
            },
            {},
            None,
        )

        response = self.loop.run_until_complete(crud_related_resource.list(request))

        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳primary keys are missing"

        # # JsonApiException
        request = RequestRelationCollection(
            "GET",
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
            "orders",
            None,
            {
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
                "pks": "2",  # error on customer id
            },
            {},
            None,
        )
        self.collection_order.list = AsyncMock(return_value=mock_orders)
        mocked_json_serializer_get.return_value.dump = Mock(side_effect=JsonApiException)

        response = self.loop.run_until_complete(crud_related_resource.list(request))

        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳"

    # CSV
    def test_csv(self):
        mock_orders = [{"id": 10, "cost": 200}, {"id": 11, "cost": 201}]

        request = RequestRelationCollection(
            "GET",
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
            "orders",
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
        crud_related_resource = CrudRelatedResource(self.datasource, self.permission_service, self.options)
        self.collection_order.list = AsyncMock(return_value=mock_orders)

        response = self.loop.run_until_complete(crud_related_resource.csv(request))

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
        crud_related_resource = CrudRelatedResource(self.datasource, self.permission_service, self.options)

        # Relation Type
        request = RequestRelationCollection(
            "GET",
            self.collection_customer,
            self.collection_order,
            OneToMany(
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

        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳Unhandled relation type"

        # FilterException
        request = RequestRelationCollection(
            "GET",
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
            "orders",
            None,
            {
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
                # "pks": "2",  # error on customer id
            },
            {},
            None,
        )
        response = self.loop.run_until_complete(crud_related_resource.csv(request))

        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳primary keys are missing"

        # collectionResourceException
        request = RequestRelationCollection(
            "GET",
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
            "orders",
            None,
            {
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
                "pks": "2",  # error on customer id
            },
            {},
            None,
        )
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud_related.parse_projection_with_pks",
            side_effect=DatasourceException,
        ):
            response = self.loop.run_until_complete(crud_related_resource.csv(request))

        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳"

        # JsonApiException
        self.collection_order.list = AsyncMock(return_value=mock_orders)
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud_related.Csv.make_csv",
            side_effect=CsvException("cannot make csv"),
        ):
            response = self.loop.run_until_complete(crud_related_resource.csv(request))

        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳cannot make csv"

    # add

    def test_add(self):
        # One to Many
        request = RequestRelationCollection(
            "POST",
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
            "orders",
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
        crud_related_resource = CrudRelatedResource(self.datasource, self.permission_service, self.options)

        with patch.object(self.collection_order, "update", new_callable=AsyncMock) as mock_collection_update:
            response = self.loop.run_until_complete(crud_related_resource.add(request))

            mock_collection_update.assert_awaited()
        assert response.status == 204

        # many to Many
        request = RequestRelationCollection(
            "POST",
            self.collection_order,
            self.collection_product,
            ManyToMany(
                {
                    "through_collection": "product_order",
                    "type": FieldType.MANY_TO_MANY,
                    "foreign_collection": "product",
                    "foreign_key": "product_id",
                    "foreign_key_target": "id",
                    "origin_key_target": "id",
                    "origin_key": "order_id",
                }
            ),
            "orders",
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
        crud_related_resource = CrudRelatedResource(self.datasource, self.permission_service, self.options)

        with patch.object(self.collection_product_order, "create", new_callable=AsyncMock) as mock_collection_create:
            response = self.loop.run_until_complete(crud_related_resource.add(request))

            mock_collection_create.assert_awaited()

        assert response.status == 204

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud_related.JsonApiSerializer.get",
        return_value=Mock,
    )
    def test_add_errors(
        self,
        mocked_json_serializer_get: Mock,
    ):
        request = RequestRelationCollection(
            "POST",
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
            "orders",
            {"data": [{"id": "201", "type": "order"}]},  # body
            {
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                # "pks": "2",  # customer id
            },  # query
            {},  # header
            None,  # user
        )
        crud_related_resource = CrudRelatedResource(self.datasource, self.permission_service, self.options)

        # no_id exception
        response = self.loop.run_until_complete(crud_related_resource.add(request))

        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳primary keys are missing"

        # no date body id
        request = RequestRelationCollection(
            "POST",
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
            "orders",
            {},  # body
            {
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "pks": "2",  # customer id
            },  # query
            {},  # header
            None,  # user
        )
        response = self.loop.run_until_complete(crud_related_resource.add(request))
        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳missing target's id"

        # unpack foreign id
        request = RequestRelationCollection(
            "POST",
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
            "orders",
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

        def mocked_unpack_id(schema, pk):
            if pk != "201":
                return unpack_id(schema, pk)
            else:
                raise CollectionResourceException()

        with patch("forestadmin.agent_toolkit.resources.collections.crud_related.unpack_id", mocked_unpack_id):
            response = self.loop.run_until_complete(crud_related_resource.add(request))
        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳"

        # Unhandled relation type
        request = RequestRelationCollection(
            "POST",
            self.collection_customer,
            self.collection_order,
            OneToMany(
                {
                    "type": FieldType.ONE_TO_ONE,
                    "foreign_collection": "order",
                    "origin_key": "customer_id",
                    "origin_key_target": "id",
                }
            ),
            "orders",
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
        response = self.loop.run_until_complete(crud_related_resource.add(request))
        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳Unhandled relation type"

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud_related.ConditionTreeFactory.match_ids",
        return_value=ConditionTreeLeaf("id", Operator.EQUAL, 201),
    )
    def test_edit(self, mocked_match_id: Mock):
        crud_related_resource = CrudRelatedResource(self.datasource, self.permission_service, self.options)

        # one to one  (order & cart)
        request = RequestRelationCollection(
            "PUT",
            self.collection_order,
            self.collection_cart,
            OneToMany(
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

        assert response.status == 204
        self.collection_cart.update.assert_awaited()

        # many to one (order & customer)
        request = RequestRelationCollection(
            "PUT",
            self.collection_order,
            self.collection_customer,
            OneToMany(
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

        assert response.status == 204
        self.collection_cart.update.assert_awaited()

    def test_edit_error(self):
        crud_related_resource = CrudRelatedResource(self.datasource, self.permission_service, self.options)

        # no timezone
        request = RequestRelationCollection(
            "PUT",
            self.collection_order,
            self.collection_customer,
            OneToMany(
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
                # "timezone": "Europe/Paris",
                "pks": "2",  # customer id
            },  # query
            {},  # header
            None,  # user
        )

        response = self.loop.run_until_complete(crud_related_resource.update_list(request))
        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳Missing timezone"

        # no id
        request = RequestRelationCollection(
            "PUT",
            self.collection_order,
            self.collection_customer,
            OneToMany(
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
                # "pks": "2",  # customer id
            },  # query
            {},  # header
            None,  # user
        )

        response = self.loop.run_until_complete(crud_related_resource.update_list(request))
        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳primary keys are missing"

        # no id for relation
        request = RequestRelationCollection(
            "PUT",
            self.collection_order,
            self.collection_customer,
            OneToMany(
                {
                    "type": FieldType.MANY_TO_ONE,
                    "foreign_collection": "customer",
                    "foreign_key": "customer_id",
                    "foreign_key_target": "id",
                }
            ),
            "orders",
            {"data": {"__id": "201", "type": "customer"}},  # body
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
        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳Relation id is missing"

        # unpack_id raises Exception
        request = RequestRelationCollection(
            "PUT",
            self.collection_order,
            self.collection_customer,
            OneToMany(
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

        def mocked_unpack_id(schema, pk):
            if pk != "201":
                return unpack_id(schema, pk)
            else:
                raise CollectionResourceException()

        with patch("forestadmin.agent_toolkit.resources.collections.crud_related.unpack_id", mocked_unpack_id):
            response = self.loop.run_until_complete(crud_related_resource.update_list(request))
        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳"

        # Error in update relation
        request = RequestRelationCollection(
            "PUT",
            self.collection_order,
            self.collection_customer,
            OneToMany(
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

        with patch.object(crud_related_resource, "_update_many_to_one", side_effect=CollectionResourceException):
            response = self.loop.run_until_complete(crud_related_resource.update_list(request))
        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳"

        # Unhandled relation
        request = RequestRelationCollection(
            "PUT",
            self.collection_order,
            self.collection_customer,
            OneToMany(
                {
                    "type": FieldType.MANY_TO_MANY,
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

        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳Unhandled relation type"

    # Count

    def test_count(self):
        crud_related_resource = CrudRelatedResource(self.datasource, self.permission_service, self.options)

        request = RequestRelationCollection(
            "GET",
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
            "orders",
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
            return_value=[{"value": 1, "group": {}}],
        ) as mock_aggregate_relation:
            response = self.loop.run_until_complete(crud_related_resource.count(request))
            mock_aggregate_relation.assert_awaited()

        assert response.status == 200
        response_content = json.loads(response.body)
        assert response_content["count"] == 1

    def test_count_error(self):
        crud_related_resource = CrudRelatedResource(self.datasource, self.permission_service, self.options)
        request = RequestRelationCollection(
            "GET",
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
            "orders",
            None,
            {
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
                # "pks": "2",  # customer id
            },
            {},
            None,
        )
        response = self.loop.run_until_complete(crud_related_resource.count(request))
        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳primary keys are missing"

        request = RequestRelationCollection(
            "GET",
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
            "orders",
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
            return_value=[],
        ) as mock_aggregate_relation:
            response = self.loop.run_until_complete(crud_related_resource.count(request))
            mock_aggregate_relation.assert_awaited()
        assert response.status == 200
        response_content = json.loads(response.body)
        assert response_content["count"] == 0

    # delete_list

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud_related.ConditionTreeFactory.match_ids",
        return_value=ConditionTreeLeaf("id", Operator.EQUAL, 201),
    )
    def test_delete_list(self, mock_mach_id: Mock):
        crud_related_resource = CrudRelatedResource(self.datasource, self.permission_service, self.options)

        # disassociate one_to_many
        request = RequestRelationCollection(
            "DELETE",
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
            "orders",
            {"data": [{"id": 201, "type": "order"}]},
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
        with patch.object(
            crud_related_resource, "_delete_one_to_many", new_callable=AsyncMock
        ) as fake_delete_one_to_many:
            response = self.loop.run_until_complete(crud_related_resource.delete_list(request))
            fake_delete_one_to_many.assert_awaited()

        assert response.status == 204

        # remove many_to_many
        # many to one (order & customer)
        request = RequestRelationCollection(
            "PUT",
            self.collection_order,
            self.collection_product,
            ManyToMany(
                {
                    "type": FieldType.MANY_TO_MANY,
                    "through_collection": "product_order",
                    "foreign_collection": None,
                    "foreign_key": "product_id",
                    "foreign_key_target": "id",
                    "origin_key": "order_id",
                    "origin_key_target": "id",
                }
            ),
            "products",
            {"data": [{"id": "201", "type": "product"}]},  # body
            {
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "pks": "2",  # customer id
                "delete": "true",
            },  # query
            {},  # header
            None,  # user
        )
        with patch.object(
            crud_related_resource, "_delete_many_to_many", new_callable=AsyncMock
        ) as fake_delete_many_to_many:
            response = self.loop.run_until_complete(crud_related_resource.delete_list(request))
            fake_delete_many_to_many.assert_awaited()

        assert response.status == 204

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud_related.ConditionTreeFactory.match_ids",
        return_value=ConditionTreeLeaf("id", Operator.EQUAL, 201),
    )
    def test_delete_list_error(self, mock_mach_id: Mock):
        crud_related_resource = CrudRelatedResource(self.datasource, self.permission_service, self.options)
        request = RequestRelationCollection(
            "PUT",
            self.collection_order,
            self.collection_product,
            ManyToMany(
                {
                    "type": FieldType.MANY_TO_MANY,
                    "through_collection": "product_order",
                    "foreign_collection": None,
                    "foreign_key": "product_id",
                    "foreign_key_target": "id",
                    "origin_key": "order_id",
                    "origin_key_target": "id",
                }
            ),
            "products",
            {"data": [{"id": "201", "type": "product"}]},  # body
            {
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                # "pks": "2",  # customer id
            },  # query
            {},  # header
            None,  # user
        )
        response = self.loop.run_until_complete(crud_related_resource.delete_list(request))
        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳primary keys are missing"

        request = RequestRelationCollection(
            "PUT",
            self.collection_order,
            self.collection_product,
            ManyToMany(
                {
                    "type": FieldType.MANY_TO_MANY,
                    "through_collection": "product_order",
                    "foreign_collection": None,
                    "foreign_key": "product_id",
                    "foreign_key_target": "id",
                    "origin_key": "order_id",
                    "origin_key_target": "id",
                }
            ),
            "products",
            {"data": [{"id": "201", "type": "product"}]},  # body
            {
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "pks": "2",  # customer id
            },  # query
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
        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳"

        # unhandled relation
        request = RequestRelationCollection(
            "PUT",
            self.collection_order,
            self.collection_product,
            ManyToOne(
                {
                    "type": FieldType.MANY_TO_ONE,
                }
            ),
            "products",
            {"data": [{"id": "201", "type": "product"}]},  # body
            {
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "pks": "2",  # customer id
            },  # query
            {},  # header
            None,  # user
        )
        response = self.loop.run_until_complete(crud_related_resource.delete_list(request))
        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳Unhandled relation type"

    # _associate_one_to_many
    def test_associate_one_to_many(self):
        crud_related_resource = CrudRelatedResource(self.datasource, self.permission_service, self.options)
        request = RequestRelationCollection(
            "POST",
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
            "orders",
            None,
            {
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
                "pks": "2",
            },
            {},
            None,
        )

        response = self.loop.run_until_complete(crud_related_resource._associate_one_to_many(request, [201], 2))
        assert response.status == 204

        # errors
        request = RequestRelationCollection(
            "POST",
            self.collection_customer,
            self.collection_order,
            OneToMany(
                {
                    "type": FieldType.ONE_TO_ONE,
                    "foreign_collection": "order",
                    "origin_key": "customer_id",
                    "origin_key_target": "id",
                }
            ),
            "orders",
            None,
            {
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
                "pks": "2",
            },
            {},
            None,
        )
        response = self.loop.run_until_complete(crud_related_resource._associate_one_to_many(request, [201], 2))

        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳Unhandled relation type"

        request = RequestRelationCollection(
            "GET",
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
            "orders",
            None,
            {
                "collection_name": "customer",
                "relation_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
                "pks": "2",
            },
            {},
            None,
        )
        with patch.object(self.collection_order, "update", new_callable=AsyncMock, side_effect=DatasourceException):
            response = self.loop.run_until_complete(crud_related_resource._associate_one_to_many(request, [201], 2))

        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳"

    # _associate_many_to_many
    def test_associate_many_to_many(self):
        crud_related_resource = CrudRelatedResource(self.datasource, self.permission_service, self.options)
        request = RequestRelationCollection(
            "POST",
            self.collection_order,
            self.collection_product,
            ManyToMany(
                {
                    "through_collection": "product_order",
                    "type": FieldType.MANY_TO_MANY,
                    "foreign_collection": "product",
                    "foreign_key": "product_id",
                    "foreign_key_target": "id",
                    "origin_key_target": "id",
                    "origin_key": "order_id",
                }
            ),
            "orders",
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
        response = self.loop.run_until_complete(crud_related_resource._associate_many_to_many(request, [201], 2))
        assert response.status == 204

        request = RequestRelationCollection(
            "POST",
            self.collection_order,
            self.collection_product,
            OneToMany(
                {
                    "through_collection": "product_order",
                    "type": FieldType.ONE_TO_MANY,
                    "foreign_collection": "product",
                    "foreign_key": "product_id",
                    "foreign_key_target": "id",
                    "origin_key_target": "id",
                    "origin_key": "order_id",
                }
            ),
            "orders",
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
        response = self.loop.run_until_complete(crud_related_resource._associate_many_to_many(request, [201], 2))
        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳Unhandled relation type"

        request = RequestRelationCollection(
            "POST",
            self.collection_order,
            self.collection_product,
            ManyToMany(
                {
                    "through_collection": "product_order",
                    "type": FieldType.MANY_TO_MANY,
                    "foreign_collection": "product",
                    "foreign_key": "product_id",
                    "foreign_key_target": "id",
                    "origin_key_target": "id",
                    "origin_key": "order_id",
                }
            ),
            "orders",
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
        with patch.object(
            self.collection_product_order, "create", new_callable=AsyncMock, side_effect=DatasourceException
        ):
            response = self.loop.run_until_complete(crud_related_resource._associate_many_to_many(request, [201], 2))
        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳"

    # get_base_fk_filter
    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud_related.ConditionTreeFactory.match_ids",
        return_value=ConditionTreeLeaf("id", Operator.EQUAL, 201),
    )
    def test_get_base_fk_filter(self, mocked_match_id: Mock):
        crud_related_resource = CrudRelatedResource(self.datasource, self.permission_service, self.options)
        request = RequestRelationCollection(
            "DELETE",
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
            "orders",
            {"data": [{"id": 201, "type": "order"}]},
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
            "DELETE",
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
            "orders",
            {"data": {}},
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

        with self.assertRaises(CollectionResourceException):
            response = self.loop.run_until_complete(crud_related_resource.get_base_fk_filter(request))

        # exclude ids
        request = RequestRelationCollection(
            "DELETE",
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
            "orders",
            {"data": {"attributes": {"all_records": True, "all_records_ids_excluded": ["201"]}}},
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
    # @patch(
    #     "forestadmin.agent_toolkit.resources.collections.crud_related.ConditionTreeFactory.match_ids",
    #     return_value=ConditionTreeLeaf("id", Operator.EQUAL, 201),
    # )
    # def test_delete_one_to_many(self, mocked_match_id: Mock):
    #     crud_related_resource = CrudRelatedResource(self.datasource, self.permission_service, self.options)

    #     request = RequestRelationCollection(
    #         "DELETE",
    #         self.collection_customer,
    #         self.collection_order,
    #         OneToMany(
    #             {
    #                 "type": FieldType.ONE_TO_MANY,
    #                 "foreign_collection": "order",
    #                 "origin_key": "customer_id",
    #                 "origin_key_target": "id",
    #             }
    #         ),
    #         "orders",
    #         {"data": [{"id": 201, "type": "order"}]},
    #         {
    #             "collection_name": "customer",
    #             "relation_name": "order",
    #             "timezone": "Europe/Paris",
    #             "fields[order]": "id,cost",
    #             "pks": "2",  # customer id
    #         },
    #         {},
    #         None,
    #     )
    #     _filter = self.loop.run_until_complete(crud_related_resource.get_base_fk_filter(request))
    #     with patch.object(, 'list')
    #     response = self.loop.run_until_complete(crud_related_resource._delete_one_to_many(request, 2, False, _filter))
    #     assert response
