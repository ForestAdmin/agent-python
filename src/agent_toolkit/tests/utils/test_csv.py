import copy
from csv import DictReader
from datetime import date, datetime
from io import StringIO
from unittest import TestCase
from unittest.mock import patch

from forestadmin.agent_toolkit.utils.csv import Csv, CsvException


class TestCsv(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = [
            {
                "id": 1,
                "name": "name",
                "creation_date": date(2001, 9, 11),
                "last_seen": datetime(2023, 5, 29, 11, 11, 11, 0),
                "boolean_field": True,
                "test_field": [1, 2, 3, 4],
            },
            {
                "id": 2,
                "name": "firstname",
                "creation_date": date(2001, 9, 12),
                "last_seen": datetime(2023, 5, 30, 11, 11, 11, 0),
                "boolean_field": False,
                "test_field": "1 2 3 4",
            },
        ]

    def read_csv(self, string: StringIO):
        string.seek(0)
        reader = DictReader(string)
        data = [line for line in reader]
        return data

    def test_make_csv(self):
        ret = Csv.make_csv(copy.deepcopy(self.data), self.data[0].keys())

        data = self.read_csv(ret)
        assert len(data) == len(self.data)
        assert data[0]["id"] == str(self.data[0]["id"])
        assert data[0]["name"] == self.data[0]["name"]
        assert data[0]["creation_date"] == self.data[0]["creation_date"].strftime("%Y-%m-%d")
        assert data[0]["last_seen"] == self.data[0]["last_seen"].strftime("%Y-%m-%d %H:%M:%S")
        assert data[0]["boolean_field"] == "1"
        assert data[0]["test_field"] == ""

        assert data[1]["id"] == str(self.data[1]["id"])
        assert data[1]["name"] == self.data[1]["name"]
        assert data[1]["creation_date"] == self.data[1]["creation_date"].strftime("%Y-%m-%d")
        assert data[1]["last_seen"] == self.data[1]["last_seen"].strftime("%Y-%m-%d %H:%M:%S")
        assert data[1]["boolean_field"] == "0"
        assert data[1]["test_field"] == "1 2 3 4"

    def test_make_csv_error(self):
        with patch(
            "forestadmin.agent_toolkit.utils.csv.DictWriter.writerow", side_effect=Exception
        ) as mocked_write_row:
            self.assertRaises(CsvException, Csv.make_csv, copy.deepcopy(self.data), self.data[0].keys())

            mocked_write_row.assert_called_once()

    def test_csv_should_have_only_projection_fields_even_if_more_in_record(self):
        fieldnames = [*self.data[0].keys()]
        fieldnames.remove("boolean_field")
        ret = Csv.make_csv(copy.deepcopy(self.data), fieldnames)
        data = self.read_csv(ret)
        self.assertNotIn("boolean_field", data[0].keys())
