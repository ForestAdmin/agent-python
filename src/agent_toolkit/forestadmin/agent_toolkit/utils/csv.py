from csv import DictWriter
from datetime import date, datetime
from io import StringIO
from typing import Any, Dict, List

from forestadmin.datasource_toolkit.exceptions import ForestException
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection


class CsvException(ForestException):
    pass


class Csv:
    @staticmethod
    def make_csv(rows: List[Dict[str, Any]], projection: Projection) -> str:
        try:
            dumped_csv = StringIO()
            csv_writer = DictWriter(dumped_csv, fieldnames=projection, extrasaction="ignore")
            csv_writer.writeheader()
            for row in rows:
                csv_writer.writerow(Csv.format_field(row))
            dumped_csv.seek(0)
            return dumped_csv
        except Exception:
            raise CsvException("Cannot make a csv")

    @staticmethod
    def format_field(row: Dict[str, Any]) -> Dict[str, Any]:
        updates = {}
        for key, value in row.items():
            if isinstance(value, bool):
                updates[key] = 1 if value is True else 0

            elif isinstance(value, list):
                updates[key] = ""

            elif isinstance(value, datetime):
                updates[key] = value.strftime("%Y-%m-%d %H:%M:%S")

            elif isinstance(value, date):
                updates[key] = value.strftime("%Y-%m-%d")

            elif isinstance(value, dict):
                sub_row = Csv.format_field(value)
                for sub_name, sub_value in sub_row.items():
                    updates[f"{key}:{sub_name}"] = sub_value
            else:
                updates[key] = value

        return updates
