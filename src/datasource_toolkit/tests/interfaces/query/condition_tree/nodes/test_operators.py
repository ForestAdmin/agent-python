from forestadmin.datasource_toolkit.interfaces.fields import Operator
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.operators import UNIQUE_OPERATORS


def test_unique_operators():
    assert UNIQUE_OPERATORS == {
        Operator.EQUAL,
        Operator.NOT_EQUAL,
        Operator.LESS_THAN,
        Operator.GREATER_THAN,
        Operator.LIKE,
        Operator.NOT_CONTAINS,
        Operator.LONGER_THAN,
        Operator.SHORTER_THAN,
        Operator.INCLUDES_ALL,
    }
