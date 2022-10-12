from forestadmin.datasource_toolkit.interfaces.query.page import Page


def test_page_init():

    page = Page()
    assert page.skip == 0
    assert page.limit is None

    page2 = Page(skip=1)
    assert page2.skip == 1
    assert page2.limit is None

    page3 = Page(limit=1)
    assert page3.skip == 0
    assert page3.limit == 1

    page4 = Page(skip=0, limit=10)
    assert page4.skip == 0
    assert page4.limit == 10


def test_page_apply():

    page = Page(skip=0)
    records = [
        {
            "id": 1,
        },
        {
            "id": 2,
        },
        {
            "id": 3,
        },
        {
            "id": 4,
        },
    ]
    assert page.apply(records) == records

    page.skip = 2
    assert page.apply(records) == records[2:]

    page.skip = 0
    page.limit = 1
    assert page.apply(records) == records[0:1]
