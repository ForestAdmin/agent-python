from forestadmin.agent_toolkit.services.serializers import DumpedResult, add_search_metadata


def test_search_add_metadata_should_return_with_correct_metadata():
    fake_result: DumpedResult = {
        "data": [
            {
                "type": "address",
                "attributes": {
                    "pays": "Suisse",
                    "street": "31686 Robert Trafficway Apt. 884",
                    "city": "Palata",
                    "complete_address": "31686 Robert Trafficway Apt. 884 Palata Suisse",
                },
                "id": 1000,
                "links": {"self": "/forest/address/1000"},
            },
            {
                "type": "address",
                "attributes": {
                    "pays": "Suisse",
                    "street": "4, boulevard de Bernier",
                    "city": "South Jeffrey",
                    "complete_address": "4, boulevard de Bernier South Jeffrey Suisse",
                },
                "id": 792,
                "links": {"self": "/forest/address/792"},
            },
            {
                "type": "address",
                "attributes": {
                    "pays": "Suisse",
                    "street": "788 Jennifer Land",
                    "city": "Emilymouth",
                    "complete_address": "788 Jennifer Land Emilymouth Suisse",
                },
                "id": 49,
                "links": {"self": "/forest/address/49"},
            },
        ]
    }
    result = add_search_metadata(fake_result, "suisse")

    assert result["meta"]["decorators"][0]["id"] == 1000
    assert "complete_address" in result["meta"]["decorators"][0]["search"]
    assert "pays" in result["meta"]["decorators"][0]["search"]

    assert result["meta"]["decorators"][1]["id"] == 792
    assert "complete_address" in result["meta"]["decorators"][1]["search"]
    assert "pays" in result["meta"]["decorators"][1]["search"]

    assert result["meta"]["decorators"][2]["id"] == 49
    assert "complete_address" in result["meta"]["decorators"][2]["search"]
    assert "pays" in result["meta"]["decorators"][2]["search"]


def test_search_add_metadata_should_do_nothing_if_empty_search_value():
    fake_result: DumpedResult = {
        "data": [
            {
                "type": "address",
                "attributes": {
                    "pays": "Suisse",
                    "street": "31686 Robert Trafficway Apt. 884",
                    "city": "Palata",
                    "complete_address": "31686 Robert Trafficway Apt. 884 Palata Suisse",
                },
                "id": 1000,
                "links": {"self": "/forest/address/1000"},
            },
            {
                "type": "address",
                "attributes": {
                    "pays": "Suisse",
                    "street": "4, boulevard de Bernier",
                    "city": "South Jeffrey",
                    "complete_address": "4, boulevard de Bernier South Jeffrey Suisse",
                },
                "id": 792,
                "links": {"self": "/forest/address/792"},
            },
            {
                "type": "address",
                "attributes": {
                    "pays": "Suisse",
                    "street": "788 Jennifer Land",
                    "city": "Emilymouth",
                    "complete_address": "788 Jennifer Land Emilymouth Suisse",
                },
                "id": 49,
                "links": {"self": "/forest/address/49"},
            },
        ]
    }
    result = add_search_metadata(fake_result, "")
    assert result == fake_result
    result = add_search_metadata(fake_result, "  ")
    assert result == fake_result
