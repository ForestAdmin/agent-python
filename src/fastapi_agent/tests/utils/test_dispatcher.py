import pytest
from forestadmin.flask_agent.utils.dispatcher import get_dispatcher_method


def test_get_dispatcher_method_list():
    method = get_dispatcher_method("GET", False)
    assert method == "list"

    method = get_dispatcher_method("POST", False)
    assert method == "add"

    method = get_dispatcher_method("DELETE", False)
    assert method == "delete_list"

    method = get_dispatcher_method("PUT", False)
    assert method == "update_list"


def test_get_dispatcher_method_detail():
    method = get_dispatcher_method("GET", True)
    assert method == "get"

    with pytest.raises(KeyError):
        get_dispatcher_method("POST", True)

    method = get_dispatcher_method("DELETE", True)
    assert method == "delete"

    method = get_dispatcher_method("PUT", True)
    assert method == "update"
