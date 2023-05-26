import asyncio
import importlib
import json
import sys
from unittest import TestCase
from unittest.mock import Mock, patch

if sys.version_info < (3, 8):
    from mock import AsyncMock
else:
    from unittest.mock import AsyncMock

import forestadmin.agent_toolkit.resources.collections.crud
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.resources.collections.exceptions import CollectionResourceException
from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection, RequestCollectionException
from forestadmin.agent_toolkit.services.permissions import PermissionService
from forestadmin.agent_toolkit.services.serializers.json_api import JsonApiException
from forestadmin.agent_toolkit.utils.context import Request
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource, DatasourceException
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.validations.records import RecordValidatorException


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

importlib.reload(forestadmin.agent_toolkit.resources.collections.crud)
from forestadmin.agent_toolkit.resources.collections.crud import CrudResource  # noqa: E402


class TestCrudResource(TestCase):
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
                    "type": FieldType.ONE_TO_MANY,
                },
                "status": {
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": False,
                    "type": FieldType.MANY_TO_ONE,
                    "foreign_collection": "status",
                    "foreign_key_target": "id",
                    "foreign_key": "status",
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
            "searchable": False,
            "segments": [],
        }
        cls.collection_order.schema = cls.collection_order._schema

        # status

        cls.collection_status = Mock(Collection)
        cls.collection_status._datasource = cls.datasource
        cls.collection_status.datasource = cls.datasource
        cls.collection_status.update = AsyncMock(return_value=None)
        cls.collection_status._name = "status"
        cls.collection_status.name = "status"
        cls.collection_status.get_field = lambda x: cls.collection_status._schema["fields"][x]
        cls.collection_status._schema = {
            "actions": {},
            "fields": {
                "id": {"column_type": PrimitiveType.NUMBER, "is_primary_key": True, "type": FieldType.COLUMN},
                "name": {"column_type": PrimitiveType.STRING, "is_primary_key": False, "type": FieldType.COLUMN},
            },
            "searchable": False,
            "segments": [],
        }
        cls.collection_status.schema = cls.collection_status._schema

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
            "status": cls.collection_status,
            "cart": cls.collection_cart,
        }

    # dispatch

    def test_dispatch(self):
        request = Request(
            method="GET",
            query={
                "collection_name": "order",
            },
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.options)
        crud_resource.get = AsyncMock()
        crud_resource.list = AsyncMock()
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

    @patch("forestadmin.agent_toolkit.resources.collections.crud.RequestCollection")
    def test_dispatch_error(self, mock_request_collection: Mock):
        request = Request(
            method="GET",
            query={
                "collection": "order",
            },
        )
        mock_request_collection.from_request = Mock(side_effect=RequestCollectionException("test exception"))
        crud_resource = CrudResource(self.datasource, self.permission_service, self.options)
        crud_resource.get = AsyncMock()

        response = self.loop.run_until_complete(crud_resource.dispatch(request, "get"))
        assert json.loads(response.body)["errors"][0] == "🌳🌳🌳test exception"
        assert response.status == 400

    # get

    @patch("forestadmin.agent_toolkit.resources.collections.crud.unpack_id", return_value=[10])
    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.ConditionTreeFactory.match_ids",
        return_value=ConditionTreeLeaf("id", Operator.EQUAL, 10),
    )
    @patch("forestadmin.agent_toolkit.resources.collections.crud.ProjectionFactory.all", return_value=["id", "cost"])
    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.JsonApiSerializer.get",
        return_value=Mock,
    )
    def test_get(
        self,
        mocked_json_serializer_get: Mock,
        mocked_projection_factory_all: Mock,
        mocked_match_ids: Mock,
        mocked_unpack_id: Mock,
    ):
        mock_order = {"id": 10, "cost": 200}
        self.collection_order.list = AsyncMock(return_value=[mock_order])
        request = RequestCollection(
            "GET", self.collection_order, None, {"collection_name": "order", "pks": "10"}, {}, None
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.options)
        mocked_json_serializer_get.return_value.dump = Mock(
            return_value={"data": {"type": "order", "attributes": mock_order}}
        )

        response = self.loop.run_until_complete(crud_resource.get(request))

        response_content = json.loads(response.body)
        assert response.status == 200
        assert isinstance(response_content["data"], dict)
        assert response_content["data"]["attributes"]["cost"] == mock_order["cost"]
        assert response_content["data"]["attributes"]["id"] == mock_order["id"]
        mocked_unpack_id.assert_called_once()
        self.collection_order.list.assert_awaited()

        # relations

        mocked_unpack_id.reset_mock()
        mock_order = {"id": 10, "cost": 0}
        mocked_json_serializer_get.return_value.dump = Mock(
            return_value={
                "data": {
                    "type": "order",
                    "attributes": mock_order,
                    "relationships": {
                        "products": {"data": [], "links": {"related": "/forest/order/10/relationships/products"}}
                    },
                }
            }
        )
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud.ProjectionFactory.all",
            return_value=[
                "id",
                "cost",
                "customer",
            ],
        ):
            response = self.loop.run_until_complete(crud_resource.get(request))

        response_content = json.loads(response.body)
        assert response.status == 200
        assert isinstance(response_content["data"], dict)
        assert response_content["data"]["attributes"]["cost"] == mock_order["cost"]
        assert response_content["data"]["attributes"]["id"] == mock_order["id"]
        mocked_unpack_id.assert_called_once()
        self.collection_order.list.assert_awaited()

    @patch("forestadmin.agent_toolkit.resources.collections.crud.unpack_id", return_value=[10])
    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.ConditionTreeFactory.match_ids",
        return_value=ConditionTreeLeaf("id", Operator.EQUAL, 10),
    )
    @patch("forestadmin.agent_toolkit.resources.collections.crud.ProjectionFactory.all", return_value=["id", "cost"])
    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.JsonApiSerializer.get",
        return_value=Mock,
    )
    def test_get_no_data(
        self,
        mocked_json_serializer_get: Mock,
        mocked_projection_factory_all: Mock,
        mocked_match_ids: Mock,
        mocked_unpack_id: Mock,
    ):
        self.collection_order.list = AsyncMock(return_value=[])
        request = RequestCollection(
            "GET", self.collection_order, None, {"collection_name": "order", "pks": "10"}, {}, None
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.options)

        response = self.loop.run_until_complete(crud_resource.get(request))

        assert response.status == 404
        assert response.body is None
        mocked_unpack_id.assert_called_once()
        self.collection_order.list.assert_awaited()

    @patch("forestadmin.agent_toolkit.resources.collections.crud.unpack_id", return_value=[10])
    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.ConditionTreeFactory.match_ids",
        return_value=ConditionTreeLeaf("id", Operator.EQUAL, 10),
    )
    @patch("forestadmin.agent_toolkit.resources.collections.crud.ProjectionFactory.all", return_value=["id", "cost"])
    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.JsonApiSerializer.get",
        return_value=Mock,
    )
    def test_get_errors(
        self,
        mocked_json_serializer_get: Mock,
        mocked_projection_factory_all: Mock,
        mocked_match_ids: Mock,
        mocked_unpack_id: Mock,
    ):
        mock_order = {"id": 10, "costt": 200}
        self.collection_order.list = AsyncMock(return_value=[mock_order])
        request = RequestCollection(
            "GET", self.collection_order, None, {"collection_name": "order", "pks": "10"}, {}, None
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.options)
        mocked_json_serializer_get.return_value.dump = Mock(side_effect=JsonApiException)

        response = self.loop.run_until_complete(crud_resource.get(request))

        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳"
        mocked_unpack_id.assert_called_once()
        self.collection_order.list.assert_awaited()

        mocked_unpack_id.reset_mock()

        mocked_unpack_id.side_effect = CollectionResourceException
        response = self.loop.run_until_complete(crud_resource.get(request))
        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳"
        mocked_unpack_id.assert_called_once()

    # add

    @patch("forestadmin.agent_toolkit.resources.collections.crud.RecordValidator.validate")
    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.JsonApiSerializer.get",
        return_value=Mock,
    )
    def test_add(
        self,
        mocked_json_serializer_get: Mock,
        mocked_record_validator_validate: Mock,
    ):
        mock_order = {"id": 10, "cost": 200}

        request = RequestCollection(
            "POST", self.collection_order, json.dumps(mock_order), {"collection_name": "order"}, {}, None
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.options)
        mocked_json_serializer_get.return_value.load = Mock(return_value=mock_order)
        mocked_json_serializer_get.return_value.dump = Mock(
            return_value={"data": {"type": "order", "attributes": mock_order}}
        )

        crud_resource.extract_data = AsyncMock(return_value=(mock_order, []))

        # with patch.object(self.collection_order, "get_field", new_callable=AsyncMock, return_value=(mock_order, [])):
        with patch.object(
            self.collection_order, "create", new_callable=AsyncMock, return_value=[mock_order]
        ) as mock_collection_create:
            response = self.loop.run_until_complete(crud_resource.add(request))

            mock_collection_create.assert_awaited()

        mocked_record_validator_validate.assert_called()
        response_content = json.loads(response.body)
        assert response.status == 200
        assert isinstance(response_content["data"], dict)
        assert response_content["data"]["attributes"]["cost"] == mock_order["cost"]
        assert response_content["data"]["attributes"]["id"] == mock_order["id"]
        assert response_content["data"]["type"] == "order"

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.JsonApiSerializer.get",
        return_value=Mock,
    )
    def test_add_errors(
        self,
        mocked_json_serializer_get: Mock,
    ):
        mock_order = {"id": 10, "cost": 200}

        request = RequestCollection(
            "POST", self.collection_order, json.dumps(mock_order), {"collection_name": "order"}, {}, None
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.options)
        crud_resource.extract_data = AsyncMock(return_value=(mock_order, []))

        # JsonApiException
        mocked_json_serializer_get.return_value.load = Mock(side_effect=JsonApiException)

        response = self.loop.run_until_complete(crud_resource.add(request))

        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳"

        mocked_json_serializer_get.return_value.load = Mock(return_value=mock_order)

        # RecordValidatorException
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud.RecordValidator.validate",
            side_effect=RecordValidatorException,
        ):
            response = self.loop.run_until_complete(crud_resource.add(request))
        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳"

        # DatasourceException
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud.RecordValidator.validate",
        ):
            with patch.object(self.collection_order, "create", new_callable=AsyncMock, side_effect=DatasourceException):
                response = self.loop.run_until_complete(crud_resource.add(request))
        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳"

        # CollectionResourceException
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud.RecordValidator.validate",
        ):
            with patch.object(self.collection_order, "create", new_callable=AsyncMock, return_value=[mock_order]):
                with patch.object(crud_resource, "_link_one_to_one_relations", side_effect=CollectionResourceException):
                    response = self.loop.run_until_complete(crud_resource.add(request))
        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳"

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.ConditionTreeFactory.match_ids",
        return_value=ConditionTreeLeaf("id", Operator.EQUAL, 1),
    )
    @patch("forestadmin.agent_toolkit.resources.collections.crud.RecordValidator.validate")
    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.JsonApiSerializer.get",
        return_value=Mock,
    )
    def test_add_with_relation(
        self,
        mocked_json_serializer_get: Mock,
        mocked_record_validator_validate: Mock,
        mock_match_ids: Mock,
    ):
        mock_order = {"id": 10, "cost": 200, "status": 1, "cart": 1}

        request = RequestCollection(
            "POST",
            self.collection_order,
            json.dumps(mock_order),
            {
                "collection_name": "order",
                "timezone": "Europe/Paris",
            },
            {},
            None,
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.options)
        mocked_json_serializer_get.return_value.load = Mock(return_value=mock_order)
        mocked_json_serializer_get.return_value.dump = Mock(
            return_value={"data": {"type": "order", "attributes": mock_order}}
        )

        with patch.object(
            self.collection_order, "create", new_callable=AsyncMock, return_value=[mock_order]
        ) as mock_collection_create:
            response = self.loop.run_until_complete(crud_resource.add(request))

            mock_collection_create.assert_awaited()

        mocked_record_validator_validate.assert_called()
        response_content = json.loads(response.body)
        assert response.status == 200
        assert isinstance(response_content["data"], dict)
        assert response_content["data"]["attributes"]["cost"] == mock_order["cost"]
        assert response_content["data"]["attributes"]["id"] == mock_order["id"]
        assert response_content["data"]["attributes"]["status"] == mock_order["status"]
        assert response_content["data"]["attributes"]["cart"] == mock_order["cart"]
        assert response_content["data"]["type"] == "order"
        self.collection_cart.update.assert_awaited()

        request = RequestCollection(
            "POST",
            self.collection_order,
            json.dumps(mock_order),
            {
                "collection_name": "order",
            },
            {},
            None,
        )
        with patch.object(
            self.collection_order, "create", new_callable=AsyncMock, return_value=[mock_order]
        ) as mock_collection_create:
            response = self.loop.run_until_complete(crud_resource.add(request))
            mock_collection_create.assert_awaited()

        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳Missing timezone"

    # list

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.JsonApiSerializer.get",
        return_value=Mock,
    )
    def test_list(self, mocked_json_serializer_get: Mock):
        mock_orders = [{"id": 10, "cost": 200}, {"id": 11, "cost": 201}]

        request = RequestCollection(
            "GET",
            self.collection_order,
            None,
            {
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
            },
            {},
            None,
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.options)
        mocked_json_serializer_get.return_value.dump = Mock(
            return_value={"data": {"type": "order", "attributes": mock_orders}}
        )
        self.collection_order.list = AsyncMock(return_value=mock_orders)

        response = self.loop.run_until_complete(crud_resource.list(request))

        assert response.status == 200
        response_content = json.loads(response.body)
        assert isinstance(response_content["data"], dict)
        assert len(response_content["data"]["attributes"]) == 2
        assert response_content["data"]["attributes"][0]["cost"] == mock_orders[0]["cost"]
        assert response_content["data"]["attributes"][0]["id"] == mock_orders[0]["id"]
        assert response_content["data"]["attributes"][1]["cost"] == mock_orders[1]["cost"]
        assert response_content["data"]["attributes"][1]["id"] == mock_orders[1]["id"]
        assert response_content["data"]["type"] == "order"
        self.collection_order.list.assert_awaited()

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.JsonApiSerializer.get",
        return_value=Mock,
    )
    def test_list_errors(self, mocked_json_serializer_get: Mock):
        mock_orders = [{"id": 10, "cost": 200}, {"id": 11, "cost": 201}]
        request = RequestCollection(
            "GET",
            self.collection_order,
            None,
            {
                "collection_name": "order",
                "fields[order]": "id,cost",
            },
            {},
            None,
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.options)

        # FilterException
        response = self.loop.run_until_complete(crud_resource.list(request))

        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳Missing timezone"

        # DatasourceException
        request = RequestCollection(
            "GET",
            self.collection_order,
            None,
            {
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
            },
            {},
            None,
        )
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud.parse_projection_with_pks",
            side_effect=DatasourceException,
        ):
            response = self.loop.run_until_complete(crud_resource.list(request))

        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳"

        # JsonApiException
        self.collection_order.list = AsyncMock(return_value=mock_orders)
        mocked_json_serializer_get.return_value.dump = Mock(side_effect=JsonApiException)

        response = self.loop.run_until_complete(crud_resource.list(request))

        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳"

    # count

    def test_count(self):
        request = RequestCollection(
            "GET", self.collection_order, None, {"collection_name": "order", "timezone": "Europe/Paris"}, {}, None
        )
        self.collection_order.aggregate = AsyncMock(return_value=[{"value": 1000, "group": {}}])
        crud_resource = CrudResource(self.datasource, self.permission_service, self.options)

        response = self.loop.run_until_complete(crud_resource.count(request))

        assert response.status == 200
        response_content = json.loads(response.body)
        assert isinstance(response_content, dict)
        assert response_content["count"] == 1000
        self.collection_order.aggregate.assert_called()

        self.collection_order.aggregate = AsyncMock(return_value=[])
        response = self.loop.run_until_complete(crud_resource.count(request))

        assert response.status == 200
        response_content = json.loads(response.body)
        assert response_content["count"] == 0
        self.collection_order.aggregate.assert_called()

    # edit

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.ConditionTreeFactory.match_ids",
        return_value=ConditionTreeLeaf("id", Operator.EQUAL, 10),
    )
    @patch("forestadmin.agent_toolkit.resources.collections.crud.RecordValidator.validate")
    @patch("forestadmin.agent_toolkit.resources.collections.crud.unpack_id", return_value=[10])
    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.JsonApiSerializer.get",
        return_value=Mock,
    )
    def test_edit(
        self,
        mocked_json_serializer_get: Mock,
        mocked_unpack_id: Mock,
        mocked_record_validator_validate: Mock,
        mocked_match_ids: Mock,
    ):
        mock_order = {"id": 10, "cost": 201}
        request = RequestCollection(
            "PUT",
            self.collection_order,
            {"data": {"attributes": {"cost": 201}, "relationships": {}}},
            {
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "pks": "10",
                "fields[order]": "id,cost",
            },
            {},
            None,
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.options)
        self.collection_order.list = AsyncMock(return_value=[mock_order])
        self.collection_order.update = AsyncMock()
        mocked_json_serializer_get.return_value.load = Mock(return_value=mock_order)
        mocked_json_serializer_get.return_value.dump = Mock(
            return_value={"data": {"type": "order", "attributes": mock_order}}
        )

        response = self.loop.run_until_complete(crud_resource.update(request))

        assert response.status == 200
        response_content = json.loads(response.body)
        assert isinstance(response_content["data"], dict)
        assert response_content["data"]["attributes"]["id"] == 10
        assert response_content["data"]["attributes"]["cost"] == 201
        self.collection_order.update.assert_awaited()

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.ConditionTreeFactory.match_ids",
        return_value=ConditionTreeLeaf("id", Operator.EQUAL, 10),
    )
    @patch("forestadmin.agent_toolkit.resources.collections.crud.RecordValidator.validate")
    @patch("forestadmin.agent_toolkit.resources.collections.crud.unpack_id", return_value=[10])
    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.JsonApiSerializer.get",
        return_value=Mock,
    )
    def test_edit_errors(
        self,
        mocked_json_serializer_get: Mock,
        mocked_unpack_id: Mock,
        mocked_record_validator_validate: Mock,
        mocked_match_ids: Mock,
    ):
        mock_order = {"id": 10, "cost": 201}
        self.collection_order.update = AsyncMock()
        self.collection_order.list = AsyncMock(return_value=[mock_order])
        request = RequestCollection(
            "PUT",
            self.collection_order,
            {"data": {"attributes": {"cost": 201}, "relationships": {}}},
            {
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "pks": "10",
                "fields[order]": "id,cost",
            },
            {},
            None,
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.options)

        # CollectionResourceException
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud.unpack_id", side_effect=CollectionResourceException
        ):
            response = self.loop.run_until_complete(crud_resource.update(request))
        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳"

        # JsonApiException
        mocked_json_serializer_get.return_value.load = Mock(side_effect=JsonApiException)
        response = self.loop.run_until_complete(crud_resource.update(request))
        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳"

        # RecordValidatorException
        mocked_json_serializer_get.return_value.load = Mock(return_value=mock_order)
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud.RecordValidator.validate",
            side_effect=RecordValidatorException,
        ):
            response = self.loop.run_until_complete(crud_resource.update(request))
        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳"

        # JsonApiException
        mocked_json_serializer_get.return_value.dump = Mock(side_effect=JsonApiException)
        response = self.loop.run_until_complete(crud_resource.update(request))
        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳"

    # delete

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.JsonApiSerializer.get",
        return_value=Mock,
    )
    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.ConditionTreeFactory.match_ids",
        return_value=ConditionTreeLeaf("id", Operator.EQUAL, 10),
    )
    @patch("forestadmin.agent_toolkit.resources.collections.crud.unpack_id", return_value=[10])
    def test_delete(
        self,
        mocked_json_serializer_get: Mock,
        mocked_unpack_id: Mock,
        mocked_match_ids: Mock,
    ):
        request = RequestCollection(
            "DELETE",
            self.collection_order,
            None,
            {"collection_name": "order", "timezone": "Europe/Paris", "pks": "10"},
            {},
            None,
        )
        self.collection_order.delete = AsyncMock()
        crud_resource = CrudResource(self.datasource, self.permission_service, self.options)
        response = self.loop.run_until_complete(crud_resource.delete(request))

        assert response.status == 204
        self.collection_order.delete.assert_awaited()

    def test_delete_error(self):
        request = RequestCollection(
            "DELETE",
            self.collection_order,
            None,
            {"collection_name": "order", "timezone": "Europe/Paris", "pks": "10"},
            {},
            None,
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.options)

        # CollectionResourceException
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud.unpack_id", side_effect=CollectionResourceException
        ):
            response = self.loop.run_until_complete(crud_resource.delete(request))

        assert response.status == 400
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == "🌳🌳🌳"

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.ConditionTreeFactory.match_ids",
        return_value=ConditionTreeLeaf("id", Operator.NOT_EQUAL, 10),
    )
    def test_delete_list(
        self,
        mocked_match_ids: Mock,
    ):
        request = RequestCollection(
            "DELETE",
            self.collection_order,
            {"data": {"attributes": {"all_records": True, "all_records_ids_excluded": [10]}}},
            {"collection_name": "order", "timezone": "Europe/Paris", "pks": "10"},
            {},
            None,
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.options)
        self.collection_order.delete = AsyncMock()

        response = self.loop.run_until_complete(crud_resource.delete_list(request))

        assert response.status == 204
        self.collection_order.delete.assert_awaited()
