import json

import requests

if __name__ == "__main__":

    r = requests.post("http://localhost:1234/", json.dumps({"method": "handshake", "collection": "", "params": {}}))
    print("handshake", r.json())

    r = requests.post(
        "http://localhost:1234/",
        json.dumps(
            {
                "method": "list",
                "collection": "child",
                "params": {
                    "filter": {
                        "condition_tree": {"field": "id", "operator": "equal", "value": 1},
                    },
                    "projection": ["id", "first_name", "age"],
                },
            }
        ),
    )
    print("list", r.json())

    r = requests.post(
        "http://localhost:1234/",
        json.dumps(
            {
                "method": "update",
                "collection": "child",
                "params": {
                    "filter": {
                        "condition_tree": {"field": "id", "operator": "equal", "value": 1},
                    },
                    "patch": {
                        "age": 120,
                    },
                },
            }
        ),
    )
    print("update", r.json())

    r = requests.post(
        "http://localhost:1234/",
        json.dumps(
            {"method": "create", "collection": "child", "params": {"data": [{"age": 12, "first_name": "toto"}]}}
        ),
    )
    print("create", r.json())

    r = requests.post(
        "http://localhost:1234/",
        json.dumps(
            {
                "method": "delete",
                "collection": "child",
                "params": {
                    "filter": {
                        "condition_tree": {"field": "id", "operator": "equal", "value": 25},
                    }
                },
            }
        ),
    )
    print("delete", r.json())
