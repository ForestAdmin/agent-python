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

import forestadmin.agent_toolkit.resources.collections.crud
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.resources.collections.exceptions import CollectionResourceException
from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection, RequestCollectionException
from forestadmin.agent_toolkit.services.permissions.ip_whitelist_service import IpWhiteListService
from forestadmin.agent_toolkit.services.permissions.permission_service import PermissionService
from forestadmin.agent_toolkit.services.serializers.json_api import (
    JsonApiException,
    JsonApiSerializer,
    create_json_api_schema,
)
from forestadmin.agent_toolkit.utils.context import Request, RequestMethod, User
from forestadmin.agent_toolkit.utils.csv import CsvException
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource, DatasourceException
from forestadmin.datasource_toolkit.exceptions import ValidationError
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.validations.records import RecordValidatorException


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
                "status": {
                    "type": FieldType.MANY_TO_ONE,
                    "foreign_collection": "status",
                    "foreign_key_target": "id",
                    "foreign_key": "status",
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
                    "foreign_type_field": "taggable_type",
                },
            },
        )

    @classmethod
    def setUpClass(cls) -> None:
        JsonApiSerializer.schema = {}
        cls.loop = asyncio.new_event_loop()
        cls.options = Options(
            auth_secret="fake_secret",
            env_secret="fake_secret",
            server_url="http://fake:5000",
            prefix="",
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
            "product": cls.collection_product,
            "tag": cls.collection_tag,
        }
        for collection in cls.datasource.collections:
            create_json_api_schema(collection)

    def setUp(self):
        self.ip_white_list_service = Mock(IpWhiteListService)
        self.ip_white_list_service.is_enable = AsyncMock(return_value=False)

        self.permission_service = Mock(PermissionService)
        self.permission_service.get_scope = AsyncMock(return_value=ConditionTreeLeaf("id", Operator.GREATER_THAN, 0))
        self.permission_service.can = AsyncMock(return_value=None)

    @classmethod
    def tearDownClass(cls) -> None:
        JsonApiSerializer.schema = {}
        return super().tearDownClass()

    # dispatch
    def test_dispatch(self):
        request = Request(
            method=RequestMethod.GET,
            query={
                "collection_name": "order",
            },
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)
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
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)
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
    @patch("forestadmin.agent_toolkit.resources.collections.crud.unpack_id", return_value=[10])
    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.ConditionTreeFactory.match_ids",
        return_value=ConditionTreeLeaf("id", Operator.EQUAL, 10),
    )
    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.ProjectionFactory.all",
        return_value=Projection("id", "cost"),
    )
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
            RequestMethod.GET, self.collection_order, None, {"collection_name": "order", "pks": "10"}, {}, None
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)
        mocked_json_serializer_get.return_value.dump = Mock(
            return_value={"data": {"type": "order", "attributes": mock_order}}
        )

        response = self.loop.run_until_complete(crud_resource.get(request))

        self.permission_service.can.assert_any_await(request.user, request.collection, "read")
        self.permission_service.can.reset_mock()
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

        response = self.loop.run_until_complete(crud_resource.get(request))

        self.permission_service.can.assert_any_await(request.user, request.collection, "read")
        self.permission_service.can.reset_mock()
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
    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.ProjectionFactory.all",
        return_value=Projection("id", "cost"),
    )
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
            RequestMethod.GET, self.collection_order, None, {"collection_name": "order", "pks": "10"}, {}, None
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)

        response = self.loop.run_until_complete(crud_resource.get(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "read")
        self.permission_service.can.reset_mock()

        assert response.status == 404
        assert response.body is None
        mocked_unpack_id.assert_called_once()
        self.collection_order.list.assert_awaited()

    @patch("forestadmin.agent_toolkit.resources.collections.crud.unpack_id", return_value=[10])
    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.ConditionTreeFactory.match_ids",
        return_value=ConditionTreeLeaf("id", Operator.EQUAL, 10),
    )
    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.ProjectionFactory.all",
        return_value=Projection("id", "cost"),
    )
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
            RequestMethod.GET, self.collection_order, None, {"collection_name": "order", "pks": "10"}, {}, None
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)
        mocked_json_serializer_get.return_value.dump = Mock(side_effect=JsonApiException)

        response = self.loop.run_until_complete(crud_resource.get(request))

        self.permission_service.can.assert_any_await(request.user, request.collection, "read")
        self.permission_service.can.reset_mock()
        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "JsonApiException",
            "detail": "🌳🌳🌳",
            "status": 500,
        }
        mocked_unpack_id.assert_called_once()
        self.collection_order.list.assert_awaited()

        mocked_unpack_id.reset_mock()

        mocked_unpack_id.side_effect = CollectionResourceException
        response = self.loop.run_until_complete(crud_resource.get(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "read")
        self.permission_service.can.reset_mock()
        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "CollectionResourceException",
            "detail": "🌳🌳🌳",
            "status": 500,
        }
        mocked_unpack_id.assert_called_once()

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.JsonApiSerializer.get",
        return_value=Mock,
    )
    def test_get_with_polymorphic_relation_should_add_projection_star(self, mocked_json_serializer_get: Mock):
        request = RequestCollection(
            RequestMethod.GET, self.collection_tag, None, {"collection_name": "tag", "pks": "10"}, {}, None
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)
        mocked_json_serializer_get.return_value.dump = Mock(
            return_value={
                "data": {"type": "tag", "attributes": {"id": 10, "taggable_id": 10, "taggable_type": "product"}},
                "included": [{"id": 10, "attributes": {"name": "my product"}}],
            }
        )
        with patch.object(
            self.collection_tag,
            "list",
            new_callable=AsyncMock,
            return_value=[
                {"id": 10, "taggable_id": 10, "taggable_type": "product", "taggable": {"id": 10, "name": "my product"}}
            ],
        ) as mock_list:
            self.loop.run_until_complete(crud_resource.get(request))

            mock_list.assert_awaited_with(ANY, ANY, ["id", "tag", "taggable_id", "taggable_type", "taggable:*"])

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
            RequestMethod.POST, self.collection_order, json.dumps(mock_order), {"collection_name": "order"}, {}, None
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)
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
        self.permission_service.can.assert_any_await(request.user, request.collection, "add")
        self.permission_service.can.reset_mock()

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
            RequestMethod.POST, self.collection_order, json.dumps(mock_order), {"collection_name": "order"}, {}, None
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)
        crud_resource.extract_data = AsyncMock(return_value=(mock_order, []))

        # JsonApiException
        mocked_json_serializer_get.return_value.load = Mock(side_effect=JsonApiException)

        response = self.loop.run_until_complete(crud_resource.add(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "add")
        self.permission_service.can.reset_mock()

        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "JsonApiException",
            "detail": "🌳🌳🌳",
            "status": 500,
        }

        mocked_json_serializer_get.return_value.load = Mock(return_value=mock_order)

        # RecordValidatorException
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud.RecordValidator.validate",
            side_effect=RecordValidatorException,
        ):
            response = self.loop.run_until_complete(crud_resource.add(request))
        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "RecordValidatorException",
            "detail": "🌳🌳🌳",
            "status": 500,
        }

        # DatasourceException
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud.RecordValidator.validate",
        ):
            with patch.object(self.collection_order, "create", new_callable=AsyncMock, side_effect=DatasourceException):
                response = self.loop.run_until_complete(crud_resource.add(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "add")
        self.permission_service.can.reset_mock()
        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "DatasourceException",
            "detail": "🌳🌳🌳",
            "status": 500,
        }

        # CollectionResourceException
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud.RecordValidator.validate",
        ):
            with patch.object(self.collection_order, "create", new_callable=AsyncMock, return_value=[mock_order]):
                with patch.object(crud_resource, "_link_one_to_one_relations", side_effect=CollectionResourceException):
                    response = self.loop.run_until_complete(crud_resource.add(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "add")
        self.permission_service.can.reset_mock()
        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "CollectionResourceException",
            "detail": "🌳🌳🌳",
            "status": 500,
        }

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
            RequestMethod.POST,
            self.collection_order,
            json.dumps(mock_order),
            {
                "collection_name": "order",
                "timezone": "Europe/Paris",
            },
            {},
            None,
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)
        mocked_json_serializer_get.return_value.load = Mock(return_value=mock_order)
        mocked_json_serializer_get.return_value.dump = Mock(
            return_value={"data": {"type": "order", "attributes": mock_order}}
        )

        with patch.object(
            self.collection_order, "create", new_callable=AsyncMock, return_value=[mock_order]
        ) as mock_collection_create:
            response = self.loop.run_until_complete(crud_resource.add(request))

            mock_collection_create.assert_awaited()
        self.permission_service.can.assert_any_await(request.user, request.collection, "add")
        self.permission_service.can.reset_mock()

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
            RequestMethod.POST,
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
        self.permission_service.can.assert_any_await(request.user, request.collection, "add")
        self.permission_service.can.reset_mock()

        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "CollectionResourceException",
            "detail": "🌳🌳🌳Missing timezone",
            "status": 500,
        }

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.JsonApiSerializer.get",
        return_value=Mock,
    )
    def test_add_should_create_and_associate_polymorphic_many_to_one(self, mocked_json_serializer_get: Mock):
        request = RequestCollection(
            RequestMethod.POST,
            self.collection_tag,
            {
                "data": {
                    "attributes": {"tag": "Good"},
                    "relationships": {"taggable": {"data": [{"type": "order", "id": "14"}]}},
                },
            },  # body
            {
                "collection_name": "order",
                "relation_name": "tags",
                "timezone": "Europe/Paris",
            },  # query
            {},  # header
            None,  # user
        )
        mocked_json_serializer_get.return_value.load = Mock(
            return_value={"taggable_id": 14, "taggable_type": "order", "tag": "aaaaa"}
        )
        mocked_json_serializer_get.return_value.dump = Mock(return_value={})
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)

        with patch.object(
            self.collection_tag, "create", new_callable=AsyncMock, return_value=[{}]
        ) as mock_collection_create:
            self.loop.run_until_complete(crud_resource.add(request))
            mock_collection_create.assert_awaited_once_with(
                ANY, [{"taggable_id": 14, "taggable_type": "order", "tag": "aaaaa"}]
            )

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.JsonApiSerializer.get",
        return_value=Mock,
    )
    def test_add_should_create_and_associate_polymorphic_one_to_one(self, mocked_json_serializer_get: Mock):
        request = RequestCollection(
            RequestMethod.POST,
            self.collection_order,
            {
                "data": {
                    "attributes": {"cost": 12.3, "important": True},
                    "relationships": {"tags": {"data": {"type": "tag", "id": "22"}}},
                },
            },  # body
            {
                "collection_name": "order",
                "relation_name": "tags",
                "timezone": "Europe/Paris",
            },  # query
            {},  # header
            None,  # user
        )

        mocked_json_serializer_get.return_value.load = Mock(return_value={"cost": 12.3, "important": True, "tags": 22})
        mocked_json_serializer_get.return_value.dump = Mock(return_value={})

        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)
        with patch.object(
            self.collection_order,
            "create",
            new_callable=AsyncMock,
            return_value=[{"cost": 12.3, "important": True, "id": 12}],
        ) as mock_collection_order_create:
            with patch.object(self.collection_tag, "update", new_callable=AsyncMock) as mock_collection_tag_update:
                self.loop.run_until_complete(crud_resource.add(request))
                mock_collection_order_create.assert_awaited_once_with(ANY, [{"cost": 12.3, "important": True}])

                # first update to break potential old link to current record (should do nothing)
                first_call_update_args = mock_collection_tag_update.await_args_list[0].args
                self.assertIn(
                    ConditionTreeLeaf("taggable_id", "equal", 12),
                    first_call_update_args[1].condition_tree.conditions,
                )
                self.assertIn(
                    ConditionTreeLeaf("taggable_type", "equal", "order"),
                    first_call_update_args[1].condition_tree.conditions,
                )
                self.assertEqual(first_call_update_args[2], {"taggable_id": None, "taggable_type": None})

                # second update to link the 1 to 1
                second_call_update_args = mock_collection_tag_update.await_args_list[1].args

                self.assertIn(
                    ConditionTreeLeaf("id", "equal", 22),
                    second_call_update_args[1].condition_tree.conditions,
                )
                self.assertEqual(second_call_update_args[2], {"taggable_id": 12, "taggable_type": "order"})

    # list
    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.JsonApiSerializer.get",
        return_value=Mock,
    )
    def test_list(self, mocked_json_serializer_get: Mock):
        mock_orders = [{"id": 10, "cost": 200}, {"id": 11, "cost": 201}]

        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            None,
            {
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
                "search": "20",
            },
            {},
            None,
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)
        mocked_json_serializer_get.return_value.dump = Mock(
            return_value={
                "data": [
                    {"type": "order", "attributes": mock_order, "id": mock_order["id"]} for mock_order in mock_orders
                ]
            }
        )
        self.collection_order.list = AsyncMock(return_value=mock_orders)

        response = self.loop.run_until_complete(crud_resource.list(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "browse")
        self.permission_service.can.reset_mock()

        assert response.status == 200
        response_content = json.loads(response.body)
        assert isinstance(response_content["data"], list)
        assert len(response_content["data"]) == 2
        assert response_content["data"][0]["type"] == "order"
        assert response_content["data"][0]["attributes"]["cost"] == mock_orders[0]["cost"]
        assert response_content["data"][0]["attributes"]["id"] == mock_orders[0]["id"]
        assert response_content["data"][1]["type"] == "order"
        assert response_content["data"][1]["attributes"]["cost"] == mock_orders[1]["cost"]
        assert response_content["data"][1]["attributes"]["id"] == mock_orders[1]["id"]
        self.collection_order.list.assert_awaited()

        assert response_content["meta"]["decorators"]["0"] == {"id": 10, "search": ["cost"]}
        assert response_content["meta"]["decorators"]["1"] == {"id": 11, "search": ["cost"]}

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.JsonApiSerializer.get",
        return_value=Mock,
    )
    def test_list_with_polymorphic_many_to_one_should_query_all_relation_record_columns(
        self, mocked_json_serializer_get: Mock
    ):
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)
        mocked_json_serializer_get.return_value.dump = Mock(
            return_value={
                "data": [
                    {
                        "type": "tag",
                        "attributes": {
                            "taggable_id": 11,
                            "taggable_type": "order",
                        },
                        "id": 1,
                        "relationships": {
                            "taggable": {
                                "data": {
                                    "id": 10,
                                    "type": "order",
                                },
                                "links": {"related": {"href": "/forest/tag/1/relationships/taggable"}},
                            }
                        },
                    },
                ],
                "included": [
                    {
                        "type": "order",
                        "id": 11,
                        "attributes": {
                            "id": 11,
                            "cost": 201,
                            "important": True,
                        },
                        "relationships": [
                            {
                                "tags": {"link": {"related": {"href": "/forest/order/11/relationships/tags"}}},
                                "cart": {"link": {"related": {"href": "/forest/order/11/relationships/cart"}}},
                                "status": {"link": {"related": {"href": "/forest/order/11/relationships/status"}}},
                                "products": {"link": {"related": {"href": "/forest/order/11/relationships/products"}}},
                            }
                        ],
                    }
                ],
            }
        )
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_tag,
            None,
            {
                "collection_name": "tag",
                "fields[tags]": "id,taggable,taggable_id,taggable_type",
                "timezone": "Europe/Paris",
            },
            {},
            None,
        )

        with patch.object(
            self.collection_tag,
            "list",
            new_callable=AsyncMock,
            return_value=[
                {"id": 1, "taggable_id": 11, "taggable_type": "order", "taggable": {}},
            ],
        ) as mock_list:
            self.loop.run_until_complete(crud_resource.list(request))
            mock_list.assert_awaited_once()
            list_args = mock_list.await_args_list[0].args
            self.assertIn("taggable:*", list_args[2])

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.JsonApiSerializer.get",
        return_value=Mock,
    )
    def test_list_should_parse_multi_field_sorting(self, mocked_json_serializer_get: Mock):
        mock_orders = [
            {"id": 10, "cost": 200, "important": "02_PENDING"},
            {"id": 11, "cost": 201, "important": "02_PENDING"},
            {"id": 13, "cost": 20, "important": "01_URGENT"},
        ]
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            None,
            {
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost,important",
                "search": "20",
                "sort": "important,-cost",
            },
            {},
            None,
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)
        mocked_json_serializer_get.return_value.dump = Mock(
            return_value={
                "data": [
                    {"type": "order", "attributes": mock_order, "id": mock_order["id"]} for mock_order in mock_orders
                ]
            }
        )
        self.collection_order.list = AsyncMock(return_value=mock_orders)
        self.loop.run_until_complete(crud_resource.list(request))

        self.collection_order.list.assert_awaited()

        paginated_filter = self.collection_order.list.await_args[0][1]
        self.assertEqual(len(paginated_filter.sort), 2)
        self.assertEqual(paginated_filter.sort[0], {"field": "important", "ascending": True})
        self.assertEqual(paginated_filter.sort[1], {"field": "cost", "ascending": False})

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.JsonApiSerializer.get",
        return_value=Mock,
    )
    def test_list_errors(self, mocked_json_serializer_get: Mock):
        mock_orders = [{"id": 10, "cost": 200}, {"id": 11, "cost": 201}]
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            None,
            {
                "collection_name": "order",
                "fields[order]": "id,cost",
            },
            {},
            None,
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)

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

        # DatasourceException
        request = RequestCollection(
            RequestMethod.GET,
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

        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "DatasourceException",
            "detail": "🌳🌳🌳",
            "status": 500,
        }

        # JsonApiException
        self.collection_order.list = AsyncMock(return_value=mock_orders)
        mocked_json_serializer_get.return_value.dump = Mock(side_effect=JsonApiException)

        response = self.loop.run_until_complete(crud_resource.list(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "browse")
        self.permission_service.can.reset_mock()

        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "name": "JsonApiException",
            "detail": "🌳🌳🌳",
            "status": 500,
        }

    # count
    def test_count(self):
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            None,
            {"collection_name": "order", "timezone": "Europe/Paris"},
            {},
            None,
        )
        self.collection_order.aggregate = AsyncMock(return_value=[{"value": 1000, "group": {}}])
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)

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

    def test_deactivate_count(self):
        request = RequestCollection(
            RequestMethod.GET,
            self.collection_order,
            None,
            {"collection_name": "order", "timezone": "Europe/Paris"},
            {},
            None,
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)

        self.collection_order._schema["countable"] = False
        response = self.loop.run_until_complete(crud_resource.count(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "browse")
        self.permission_service.can.reset_mock()
        self.collection_order._schema["countable"] = True

        assert response.status == 200
        response_content = json.loads(response.body)
        assert response_content["meta"]["count"] == "deactivated"

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
            RequestMethod.PUT,
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
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)
        self.collection_order.list = AsyncMock(return_value=[mock_order])
        self.collection_order.update = AsyncMock()
        mocked_json_serializer_get.return_value.load = Mock(return_value=mock_order)
        mocked_json_serializer_get.return_value.dump = Mock(
            return_value={"data": {"type": "order", "attributes": mock_order}}
        )

        response = self.loop.run_until_complete(crud_resource.update(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()

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
            RequestMethod.PUT,
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
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)

        # CollectionResourceException
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud.unpack_id", side_effect=CollectionResourceException
        ):
            response = self.loop.run_until_complete(crud_resource.update(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()
        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {
            "detail": "🌳🌳🌳",
            "name": "CollectionResourceException",
            "status": 500,
        }

        # JsonApiException
        mocked_json_serializer_get.return_value.load = Mock(side_effect=JsonApiException)
        response = self.loop.run_until_complete(crud_resource.update(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()
        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {"detail": "🌳🌳🌳", "name": "JsonApiException", "status": 500}

        # RecordValidatorException
        mocked_json_serializer_get.return_value.load = Mock(return_value=mock_order)
        with patch(
            "forestadmin.agent_toolkit.resources.collections.crud.RecordValidator.validate",
            side_effect=RecordValidatorException,
        ):
            response = self.loop.run_until_complete(crud_resource.update(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()
        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {"detail": "🌳🌳🌳", "name": "RecordValidatorException", "status": 500}

        # JsonApiException
        mocked_json_serializer_get.return_value.dump = Mock(side_effect=JsonApiException)
        response = self.loop.run_until_complete(crud_resource.update(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "edit")
        self.permission_service.can.reset_mock()
        assert response.status == 500
        response_content = json.loads(response.body)
        assert response_content["errors"][0] == {"detail": "🌳🌳🌳", "name": "JsonApiException", "status": 500}

    def test_edit_should_not_update_pk_if_not_set_in_attributes(self):
        request = RequestCollection(
            RequestMethod.PUT,
            self.collection_order,
            {"data": {"attributes": {"cost": 201}, "id": 10, "relationships": {}}},
            {
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "pks": "10",
                "fields[order]": "id,cost",
            },
            {},
            None,
        )
        mock_order = {"id": 10, "cost": 201}
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)
        self.collection_order.list = AsyncMock(return_value=[mock_order])
        self.collection_order.update = AsyncMock()

        self.loop.run_until_complete(crud_resource.update(request))
        self.permission_service.can.reset_mock()
        self.collection_order.update.assert_any_await(ANY, ANY, {"cost": 201})

    def test_edit_should_update_pk_if_set_in_attributes(self):
        request = RequestCollection(
            RequestMethod.PUT,
            self.collection_order,
            {"data": {"attributes": {"cost": 201, "id": 11}, "id": 10, "relationships": {}}},
            {
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "pks": "10",
                "fields[order]": "id,cost",
            },
            {},
            None,
        )
        mock_order = {"id": 11, "cost": 201}
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)
        self.collection_order.list = AsyncMock(return_value=[mock_order])
        self.collection_order.update = AsyncMock()

        self.loop.run_until_complete(crud_resource.update(request))
        self.permission_service.can.reset_mock()
        self.collection_order.update.assert_any_await(ANY, ANY, {"cost": 201, "id": 11})

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
            RequestMethod.DELETE,
            self.collection_order,
            None,
            {"collection_name": "order", "timezone": "Europe/Paris", "pks": "10"},
            {},
            None,
        )
        self.collection_order.delete = AsyncMock()
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)
        response = self.loop.run_until_complete(crud_resource.delete(request))
        self.permission_service.can.assert_any_await(request.user, request.collection, "delete")
        self.permission_service.can.reset_mock()

        assert response.status == 204
        self.collection_order.delete.assert_awaited()

    def test_delete_error(self):
        request = RequestCollection(
            RequestMethod.DELETE,
            self.collection_order,
            None,
            {"collection_name": "order", "timezone": "Europe/Paris", "pks": "10"},
            {},
            None,
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)

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

    @patch(
        "forestadmin.agent_toolkit.resources.collections.crud.ConditionTreeFactory.match_ids",
        return_value=ConditionTreeLeaf("id", Operator.NOT_EQUAL, 10),
    )
    def test_delete_list(
        self,
        mocked_match_ids: Mock,
    ):
        request = RequestCollection(
            RequestMethod.DELETE,
            self.collection_order,
            {"data": {"attributes": {"all_records": True, "all_records_ids_excluded": ["10"]}}},
            {"collection_name": "order", "timezone": "Europe/Paris", "pks": "10"},
            {},
            None,
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)
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
            None,
            {
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
            },
            {},
            None,
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)
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
            None,
            {
                "collection_name": "order",
                "fields[order]": "id,cost",
            },
            {},
            None,
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)

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
            None,
            {
                "collection_name": "order",
                "timezone": "Europe/Paris",
                "fields[order]": "id,cost",
            },
            {},
            None,
        )
        crud_resource = CrudResource(self.datasource, self.permission_service, self.ip_white_list_service, self.options)
        self.collection_order.list = AsyncMock(return_value=mock_orders)

        response = self.loop.run_until_complete(crud_resource.csv(request))
        self.permission_service.can.reset_mock()

        assert response.status == 200
        self.collection_order.list.assert_awaited()
        self.assertIsNone(self.collection_order.list.await_args[0][1].page)
