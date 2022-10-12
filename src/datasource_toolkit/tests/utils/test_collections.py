from unittest import mock

from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, ManyToOne, OneToOne, PrimitiveType
from forestadmin.datasource_toolkit.utils.collections import CollectionUtils


def test_get_field_schema():
    with mock.patch.object(Collection, "__abstractmethods__", new_callable=set):
        collection = Collection(name="t", datasource=mock.MagicMock())  # type: ignore
        column_schema: Column = {
            "column_type": PrimitiveType.NUMBER,
            "type": FieldType.COLUMN,
            "filter_operators": set(),
            "default_value": None,
            "enum_values": None,
            "is_primary_key": None,
            "is_read_only": None,
            "is_sortable": None,
            "validations": None,
        }
        collection.schema["fields"] = {"c1": column_schema}  # type: ignore

        assert CollectionUtils.get_field_schema(collection, "c1") == column_schema

        mock_datasource = mock.MagicMock()
        mock_datasource.get_collection = mock.MagicMock(return_value=collection)
        collection2 = Collection(name="t2", datasource=mock_datasource)  # type: ignore
        one_to_one_schema: OneToOne = {
            "type": FieldType.ONE_TO_ONE,
            "origin_key": "t_id",
            "origin_key_target": "id",
            "foreign_collection": "t",
        }
        collection2.schema["fields"] = {"r1": one_to_one_schema}

        assert CollectionUtils.get_field_schema(collection2, "r1:c1") == column_schema

        mock_datasource = mock.MagicMock()
        mock_datasource.get_collection = mock.MagicMock(return_value=collection2)
        collection3 = Collection(name="t3", datasource=mock_datasource)  # type: ignore
        many_to_one_schema: ManyToOne = {
            "type": FieldType.MANY_TO_ONE,
            "foreign_key": "t3_id",
            "foreign_key_target": "id",
            "foreign_collection": "t2",
        }
        collection3.schema["fields"] = {"r2": many_to_one_schema}
        assert CollectionUtils.get_field_schema(collection3, "r2:r1:c1") == column_schema
