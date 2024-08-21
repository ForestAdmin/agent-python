from typing import List
from unittest import mock

import pytest
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.interfaces.fields import FieldType
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection, ProjectionException


def test_projection_columns():
    projection = Projection("c1", "c2", "r1:c1", "r1:r2:c1")
    assert projection.columns == ["c1", "c2"]


def test_projection_relations():
    projection = Projection("c1", "c2", "r1:c1", "r1:r2:c1", "r2:c1")
    assert projection.relations == {"r1": Projection("c1", "r2:c1"), "r2": Projection("c1")}


def test_replace():
    projection = Projection("c1", "c2", "r1:c1")

    def replace_handler(c: str) -> str:
        return f"replaced:{c}"

    assert projection.replace(replace_handler) == Projection("replaced:c1", "replaced:c2", "replaced:r1:c1")

    def replace_handler2(c: str) -> List[str]:
        return [c, f"n_{c}"]

    r = projection.replace(replace_handler2)
    assert r == Projection("c1", "n_c1", "c2", "n_c2", "r1:c1", "n_r1:c1")

    def replace_handler3(c: str) -> Projection:
        return Projection(c, f"n_{c}")

    r = projection.replace(replace_handler3)
    assert r == Projection("c1", "n_c1", "c2", "n_c2", "r1:c1", "n_r1:c1")


def test_union():
    projection = Projection("a", "c", "b")
    assert projection.union(Projection("a", "z", "x")) == Projection("a", "c", "b", "z", "x")


def test_reproject():
    projection = Projection("c1", "c2", "r1:c1")

    result = projection._reproject({"c1": "v1", "c2": "v2", "r1": {"c1": "r1c1"}})  # type: ignore
    assert result == {"c1": "v1", "c2": "v2", "r1": {"c1": "r1c1"}}

    result = projection._reproject(
        {"c3": "v3", "c4": "v4", "c1": "v1", "c2": "v2", "r1": {"c1": "r1c1"}}  # type: ignore
    )
    assert result == {"c1": "v1", "c2": "v2", "r1": {"c1": "r1c1"}}


def test_apply():
    projection = Projection("c1", "c2", "r1:c1")
    with mock.patch.object(projection, "_reproject") as mock_reproject:
        mock_reproject.side_effect = [1, 2]
        assert projection.apply([{"1": 1}, {"2": 2}]) == [1, 2]
        mock_reproject.assert_has_calls([mock.call({"1": 1}), mock.call({"2": 2})])


@mock.patch("forestadmin.datasource_toolkit.utils.schema.SchemaUtils.get_primary_keys")
@mock.patch("forestadmin.datasource_toolkit.datasources.Datasource.get_collection")
def test_with_pks(mock_get_collection: mock.MagicMock, mock_get_pk: mock.MagicMock):
    projection = Projection("c1", "r1:c1")
    with mock.patch.object(Collection, "__abstractmethods__", new_callable=set):
        collection = Collection(name="t", datasource=mock.MagicMock())  # type: ignore
        collection.schema["fields"] = {
            "r1": {
                "foreign_collection": "t2",
                "type": FieldType.MANY_TO_ONE,
            }
        }  # type: ignore
        collection2 = Collection(name="t2", datasource=mock.MagicMock())  # type: ignore
        collection2.schema["fields"] = {}
        mock_get_pk.return_value = ["cid"]
        mock_get_collection.return_value = collection2
        assert projection.with_pks(collection) == ["c1", "r1:c1", "cid", "r1:cid"]

        projection = Projection("c1", "r1:c1", "cid")
        assert projection.with_pks(collection) == ["c1", "r1:c1", "cid", "r1:cid"]


def test_nest():
    projection = Projection("c1", "c2", "r1:c1")
    assert projection.nest("") == Projection("c1", "c2", "r1:c1")

    assert projection.nest("r2") == Projection("r2:c1", "r2:c2", "r2:r1:c1")


def test_unnest():
    projection = Projection("c1", "c2", "r1:c1")

    with pytest.raises(ProjectionException):
        projection.unnest()

    projection = Projection("r1:c1", "r1:c2", "r1:c3")
    assert projection.unnest() == Projection("c1", "c2", "c3")


def test_equal():
    projection_1 = Projection("c1", "c2", "r1:c1")
    projection_2 = Projection("c2", "c1", "r1:c1")
    assert projection_1 == projection_2

    projection_3 = Projection("c2", "c3", "r1:c1")
    assert projection_1 != projection_3

    projection_1 = Projection("c1", "r1:c1")
    projection_2 = Projection("c2", "c3", "r1:c1")
    assert projection_1 != projection_2

    projection_1 = Projection("c2", "r1:c1", "c3", "c2")
    projection_2 = Projection("c2", "c3", "r1:c1")
    assert projection_1 == projection_2
