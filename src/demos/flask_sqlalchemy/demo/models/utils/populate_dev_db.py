import datetime
import random
import zoneinfo
from typing import Any, List, Set

from demo.models.models import ORDER_STATUS, Address, Base, Customer, Order
from faker import Faker
from sqlalchemy.orm import sessionmaker

fake = Faker(["it_IT", "en_US", "ja_JP", "fr_FR"])
Session = sessionmaker(Base.metadata.bind)


def _bulk_insert(items: List[Any]):
    with Session.begin() as session:  # type: ignore
        for item in items:
            session.add(item)


def _populate_customers(nb: int = 500):
    customers: List[Customer] = []
    for _ in range(0, nb):
        customers.append(
            Customer(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                age=random.choices([None, random.randint(16, 120)])[0],
            )
        )
    _bulk_insert(customers)
    return customers


def _populate_addresses(customers: List[Customer]) -> List[Address]:
    addresses: List[Address] = []

    for _ in range(0, 1000):
        address = Address(
            street=fake.street_address(), city=fake.city(), country=fake.country(), zip_code=fake.postcode()
        )
        known_customer: Set[Customer] = set()
        for _ in range(1, random.randint(2, 4)):
            customer = random.choices(customers)[0]
            if customer not in known_customer:
                known_customer.add(customer)
                address.customers.append(customer)
        addresses.append(address)
    _bulk_insert(addresses)
    return addresses


def _populate_orders(addresses: List[Address]) -> List[Order]:
    orders: List[Order] = []
    for address in addresses:
        o = Order(
            amount=random.randint(10, 10000),
            created_at=fake.date_time_between_dates(
                datetime.datetime(2021, 1, 1), datetime.datetime.utcnow(), tzinfo=zoneinfo.ZoneInfo("UTC")
            ),
            customer=address.customers[0],
            billing_address=address,
            delivering_address=address,
            status=random.choice(list(ORDER_STATUS)),
        )
        orders.append(o)
    return orders


def populate():
    customers = _populate_customers()
    addresses = _populate_addresses(customers)
    with Session.begin() as session:
        addresses = session.query(Address).select_from(Customer).join(Customer, Address.customers).all()
        orders = _populate_orders(addresses)
        for order in orders:
            session.add(order)
