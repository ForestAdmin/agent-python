import random

from app.models import Address, Cart, Customer, Order
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from faker import Faker

fake = Faker(["it_IT", "en_US", "ja_JP", "fr_FR"])


class Command(BaseCommand):
    help = "Create fake data for the database"

    # def add_arguments(self, parser):
    #     parser.add_argument("poll_ids", nargs="+", type=int)

    def handle(self, *args, **options):
        users, groups = create_users_groups()
        customers = create_customers()
        addresses = create_addresses(customers)
        orders, carts = create_orders_cart(customers, addresses)


def create_users_groups(nb_group=4, nb_users=10):
    groups = []
    users = []
    for i in range(nb_group):
        g = Group(name=fake.company())
        g.save()
        g.refresh_from_db()
        groups.append(g)

    for i in range(nb_users):
        u = User(username=f"{fake.first_name()[0]}{fake.last_name()}")
        u.save()
        u.refresh_from_db()
        u.groups.add(groups[i % (len(groups) - 1)])
        users.append(u)
    return users, groups


def create_customers(nb_customers=500):
    customers = []
    for i in range(nb_customers):
        c = Customer(first_name=fake.first_name(), last_name=fake.last_name(), birthday_date=fake.date_of_birth())
        c.save()
        c.refresh_from_db()
        customers.append(c)
    return customers


def create_addresses(customers, nb_addresses=500):
    addresses = []
    for i in range(nb_addresses):
        a = Address(
            street=fake.street_name(), number=fake.building_number(), city=fake.city(), zip_code=fake.postcode()
        )
        a.save()
        a.refresh_from_db()
        a.customers.add(customers[i % (len(customers)) - 1])
        addresses.append(a)
    return addresses


def create_orders_cart(customers, addresses, nb_order=1000):
    orders = []
    carts = []

    for i in range(nb_order):
        o = Order(
            amount=random.randint(0, 100000) / 100,
            customer=customers[i % (len(customers) - 1)],
            billing_address=addresses[i % (len(addresses) - 1)],
            delivering_address=addresses[i % (len(addresses) - 1)],
            status=random.choice(list(Order.OrderStatus)),
        )
        o.save()
        o.refresh_from_db()
        orders.append(o)

        c = Cart(name=fake.city(), customer=customers[i % (len(customers) - 1)], order=o)
        c.save()
        c.refresh_from_db()
        carts.append(c)
    return orders, carts
