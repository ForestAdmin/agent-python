import asyncio
from unittest import TestCase
from unittest.mock import AsyncMock

from forestadmin.datasource_toolkit.decorators.computed.utils.deduplication import transform_unique_values


class TestDeduplication(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()

    def test_transform_unique_values(self):
        async def transformers(items):
            return [value * 2 for value in items]

        handler = AsyncMock(wraps=transformers)
        inputs = [1, None, 2, 2, None, 666]
        results = self.loop.run_until_complete(transform_unique_values(inputs, handler))
        self.assertEqual(results, [2, None, 4, 4, None, 1332])
        handler.assert_awaited_once_with([1, 2, 666])
