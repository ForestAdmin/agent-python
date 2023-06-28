import asyncio
from unittest import TestCase

from forestadmin.datasource_toolkit.decorators.computed.utils import flatten, transform_unique_values, unflatten
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection


class TestComputedUtilsDecorator(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()

    def test_transform_unique_values(self):
        async def transformers(items):
            return [value * 2 for value in items]

        inputs = [1, None, 2, 2, None, 666]
        results = self.loop.run_until_complete(transform_unique_values(inputs, transformers))
        assert results == [2, None, 4, 4, None, 1332]

    def test_unflatten_simple(self):
        flat_list = [[1, 2, 3], ["Romain", None, "Ana"]]
        projection = Projection("id", "book:author:first_name")

        unflat = unflatten(flat_list, projection)

        assert unflat[0] == {"id": 1, "book": {"author": {"first_name": "Romain"}}}
        assert unflat[1] == {"id": 2, "book": None}
        assert unflat[2] == {"id": 3, "book": {"author": {"first_name": "Ana"}}}

    def test_unflatten_multi_null(self):
        flat_list = [[None], [15], [26], [None]]
        projection = Projection(
            "rental:customer:name",
            "rental:id",
            "rental:number_of_days",
            "rental:customer:id",
        )
        unflat = unflatten(flat_list, projection)
        assert unflat[0] == {"rental": {"id": 15, "number_of_days": 26, "customer": None}}

    def test_flatten(self):
        records = [
            {"id": 1, "book": {"author": {"first_name": "Romain"}}},
            {"id": 2, "book": None},
            {"id": 3, "book": {"author": {"first_name": "Ana"}}},
        ]
        projection = Projection("id", "book:author:first_name")
        results = flatten(records, projection)
        assert results == [[1, 2, 3], ["Romain", None, "Ana"]]
