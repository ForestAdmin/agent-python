from unittest import TestCase

from forestadmin.datasource_toolkit.decorators.computed.utils.flattener import (
    _Undefined,
    flatten,
    unflatten,
    with_null_markers,
)
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection


class TestFlatten(TestCase):
    def test_flatten(self):
        records = [
            {"id": 1, "book": {"author": {"first_name": "Romain"}}},
            {"id": 2, "book": None},
            {"id": 3, "book": {"author": {"first_name": "Ana"}}},
        ]
        projection = Projection("id", "book:author:first_name")
        results = flatten(records, projection)

        self.assertEqual(results, [[1, 2, 3], ["Romain", _Undefined(), "Ana"]])

    def test_flatten_with_null_marker(self):
        records = [
            {"id": 1, "book": {"author": {"first_name": "Romain"}}},
            {"id": 2, "book": None},
            {"id": 3, "book": {"author": {"first_name": "Ana"}}},
        ]
        projection = Projection("id", "book:author:first_name")
        marked_projection = with_null_markers(projection)
        results = flatten(records, marked_projection)

        assert results[marked_projection.index("id")] == [1, 2, 3]
        assert results[marked_projection.index("book:author:first_name")] == ["Romain", _Undefined(), "Ana"]
        assert results[marked_projection.index("book:author:first_name")] == ["Romain", _Undefined(), "Ana"]


class TestUnflatten(TestCase):
    def test_unflatten_simple(self):
        flat_list = [
            [1, 2, 3],
            ["romain", _Undefined(), "ana"],
        ]
        projection = ["id", "book:author:firstname"]
        unflat = unflatten(flat_list, projection)

        self.assertEqual(
            unflat,
            [
                {"id": 1, "book": {"author": {"firstname": "romain"}}},
                {"id": 2},
                {"id": 3, "book": {"author": {"firstname": "ana"}}},
            ],
        )

    def test_unflatten_simple_with_marker(self):
        records = [
            {"id": 1, "book": {"category": "roman"}},
            {"id": 2, "book": None},
            {"id": 3, "book": {"category": "nouvelle"}},
        ]
        projection = Projection("id", "book:category")
        marked_projection = with_null_markers(projection)
        flat_list = flatten(records, marked_projection)

        unflat = unflatten(flat_list, marked_projection)

        assert records == unflat

    def test_unflatten_multiple_undefined(self):
        flat_list = [[_Undefined()], [15], [26], [_Undefined()]]
        projection = [
            "rental:customer:name",
            "rental:id",
            "rental:numberOfDays",
            "rental:customer:id",
        ]
        unflat = unflatten(flat_list, projection)
        self.assertEqual(unflat, [{"rental": {"id": 15, "numberOfDays": 26}}])

    def test_round_trip_with_marker_should_conserve_null_values(self):
        records = [
            {"id": 1, "book": {"author": {"firstname": "Isaac", "lastname": "Asimov"}}},
            {"id": 2, "book": {"author": None}},
            {"id": 3, "book": None},
            {"id": 4},
        ]
        projection = ["id", "book:author:firstname", "book:author:lastname"]
        marked_projection = with_null_markers(projection)

        flat_list = flatten(records, marked_projection)
        unflat = unflatten(flat_list, marked_projection)

        self.assertEqual(
            marked_projection,
            [
                "id",
                "book:author:firstname",
                "book:author:lastname",
                "book:__nullMarker",
                "book:author:__nullMarker",
            ],
        )
        self.assertEqual(
            flat_list,
            [
                [1, 2, 3, 4],  # id
                ["Isaac", _Undefined(), _Undefined(), _Undefined()],  # book:author:firstname
                ["Asimov", _Undefined(), _Undefined(), _Undefined()],  # book:author:lastname
                [_Undefined(), _Undefined(), None, _Undefined()],  # book:__nullMaker
                [_Undefined(), None, _Undefined(), _Undefined()],  # book:author:__nullMaker
            ],
        )
        self.assertEqual(records, unflat)
