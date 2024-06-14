import pytest
from forestadmin.datasource_toolkit.interfaces.actions import ActionFieldType, ActionsScope


@pytest.mark.parametrize("key,value", (("SINGLE", "Single"), ("BULK", "Bulk"), ("GLOBAL", "Global")))
def test_action_scope(key: str, value: str):
    assert ActionsScope[key].value == value


@pytest.mark.parametrize(
    "key,value",
    (
        ("BOOLEAN", "Boolean"),
        ("COLLECTION", "Collection"),
        ("DATE", "Date"),
        ("DATE_ONLY", "Dateonly"),
        ("ENUM", "Enum"),
        ("FILE", "File"),
        ("JSON", "Json"),
        ("NUMBER", "Number"),
        ("STRING", "String"),
        ("ENUM_LIST", "EnumList"),
        ("FILE_LIST", "FileList"),
        ("NUMBER_LIST", "NumberList"),
        ("STRING_LIST", "StringList"),
    ),
)
def test_action_field_type(key: str, value: str):
    assert ActionFieldType[key].value == value
