#!/usr/bin/env python

import datetime
import random
import sys
from typing import Any, List, Set, Tuple, cast
from uuid import uuid4

import typer
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import settings
from src.with_sql_alchemy.models import ORDER_STATUS, Address, Base, Cart, Customer, Order

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

fake = Faker(["it_IT", "en_US", "ja_JP", "fr_FR"])
app = typer.Typer()


@app.command()
def create():
    engine = create_engine(settings.db_uri)
    Base.metadata.create_all(engine)


@app.command()
def seed():
    engine = create_engine(settings.db_uri)
    Session = sessionmaker(engine)
    with Session.begin() as session:
        customers = _populate_customers(session)
        addresses = _populate_addresses(session, customers)

        addresses = session.query(Address).select_from(Customer).join(Customer, Address.customers).all()
        orders = _populate_orders(addresses)
        session.add_all(orders)
        orders = cast(List[Order], session.query(Order))

        orders, carts = _populate_carts(orders)
        session.add_all(carts)
        session.commit()


def _bulk_insert(session, items: List[Any]):
    # with Session.begin() as session:  # type: ignore
    for item in items:
        session.add(item)


def _populate_customers(session, nb: int = 500) -> List[Customer]:
    customers: List[Customer] = []
    for _ in range(0, nb):
        customers.append(
            Customer(
                pk=str(uuid4()).encode("utf-8"),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                birthday_date=fake.date_of_birth(),
                age=random.choices([None, random.randint(16, 120)])[0],
                is_vip=random.choice([True, False]),
            )
        )
    _bulk_insert(session, customers)
    return customers


def _populate_addresses(session, customers: List[Customer]) -> List[Address]:
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
    _bulk_insert(session, addresses)
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


def _populate_carts(orders: List[Order]) -> Tuple[List[Order], List[Cart]]:
    carts: List[Cart] = []
    for order in orders:
        c = Cart(name=fake.language_name(), pk=order.pk, order_id=order.pk)
        order.cart = c
        carts.append(c)

    return orders, carts


if __name__ == "__main__":
    app()
