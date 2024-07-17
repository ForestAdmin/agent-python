import random
from datetime import datetime, timezone
from uuid import uuid4

from app.flask_models import FlaskAddress, FlaskCart, FlaskCustomer, FlaskCustomersAddresses, FlaskOrder
from app.models import Address, Cart, Customer, CustomerAddress, Order
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

fake = Faker(["it_IT", "en_US", "ja_JP", "fr_FR"])
fr_fake = Faker(["fr_FR"])


class Command(BaseCommand):
    help = "Create fake data for the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "-b",
            "--big-data",
            help=f"create a lot of data, can take a while(~=5min)). Open this file ({__file__}) to edit the values",
            action="store_true",
        )
        parser.add_argument(
            "-o",
            "--only-other-database",
            help="only populate 'other' database",
            action="store_true",
        )
        parser.add_argument(
            "--all-databases",
            help="don't populate 'other' database",
            action="store_true",
        )

    @transaction.atomic()
    def handle(self, *args, **options):
        numbers = {
            "groups": 4,
            "users": 10,
            "customers": 500,
            "addresses": 500,
            "orders_carts": 1000,
        }
        if options["big_data"]:
            numbers = {
                "groups": 50,
                "users": 1000,
                "customers": 500000,
                "addresses": 1000000,
                "orders_carts": 3000000,
            }

        if not options["only_other_database"]:
            users, groups = create_users_groups(numbers["groups"], numbers["users"])
            if options["verbosity"] != 0:
                print(f"users({numbers['users']}) and groups({numbers['groups']}) created ")

            customers = create_customers(numbers["customers"])
            if options["verbosity"] != 0:
                print(f"customers({numbers['customers']}) created")

            addresses = create_addresses(customers, numbers["addresses"])
            if options["verbosity"] != 0:
                print(f"addresses({numbers['addresses']}) created")

            orders, carts = create_orders_cart(customers, addresses, numbers["orders_carts"])
            if options["verbosity"] != 0:
                print(f"orders and carts ({numbers['orders_carts']}) created")

        if options["all_databases"] or options["only_other_database"]:
            customers = populate_flask_customers(numbers["customers"])
            addresses = populate_flask_addresses(customers)
            populate_orders(addresses)


# main db


def create_users_groups(nb_group=4, nb_users=10):
    groups = []
    users = []
    for i in range(nb_group):
        g = Group(name=fake.company())
        groups.append(g)
    Group.objects.bulk_create(groups)
    groups = Group.objects.all()

    usernames = set()
    for i in range(nb_users):
        uname = f"{fake.first_name()[0]}{fake.last_name()}"
        while uname in usernames:
            uname = f"{fake.first_name()[0]}{fake.last_name()}"
        usernames.add(uname)
        u = User(username=uname)
        users.append(u)
    User.objects.bulk_create(users)
    users = User.objects.all()

    groups_users = []
    for i in range(1, nb_users):
        groups_users.append(User.groups.through(user_id=i, group_id=(i % nb_group) + 1))
    User.groups.through.objects.bulk_create(groups_users)

    return users, groups


def create_customers(nb_customers=500):
    customers = []
    for i in range(nb_customers):
        c = Customer(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            birthday_date=fake.date_of_birth(tzinfo=timezone.utc),
        )
        customers.append(c)
    Customer.objects.bulk_create(customers)
    customers = Customer.objects.all()
    return customers


def create_addresses(customers, nb_addresses=500):
    addresses = []
    for i in range(nb_addresses):
        a = Address(
            street=fake.street_name(),
            number=fake.building_number(),
            city=fake.city(),
            country=fake.country(),
            zip_code=fr_fake.postcode(),
        )
        addresses.append(a)
    Address.objects.bulk_create(addresses)
    addresses = Address.objects.all()

    customer_addresses = []
    nb_customer = customers.count()
    for i in range(1, nb_addresses):
        customer_addresses.append(CustomerAddress(address_id=i, customer_id=((i - 1) % nb_customer) + 1))
    CustomerAddress.objects.bulk_create(customer_addresses)

    return addresses


def create_orders_cart(customers, addresses, nb_order=1000):
    orders = []
    carts = []

    for i in range(1, nb_order + 1):
        o = Order(
            id=i,
            ordered_at=fake.date_time_between(start_date=datetime(2015, 1, 1), tzinfo=timezone.utc),
            amount=random.randint(0, 100000) / 100,
            customer=customers[i % (len(customers) - 1)],
            billing_address=addresses[i % (len(addresses) - 1)],
            delivering_address=addresses[i % (len(addresses) - 1)],
            status=random.choice(list(Order.OrderStatus)),
        )
        orders.append(o)
    Order.objects.bulk_create(orders)
    orders = Order.objects.all()

    for i in range(1, nb_order + 1):
        c = Cart(name=fake.city(), order_id=i)
        carts.append(c)
    Cart.objects.bulk_create(carts)
    carts = Cart.objects.all()
    return orders, carts


# other db


def populate_flask_customers(nb: int = 500):
    FlaskCustomer.objects.bulk_create(
        [
            FlaskCustomer(
                id=str(uuid4()).encode("utf-8"),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                birthday_date=datetime.fromordinal(fake.date_of_birth().toordinal()).replace(tzinfo=timezone.utc),
                age=random.choices([None, random.randint(16, 120)])[0],
                is_vip=random.choice([True, False]),
            )
            for i in range(nb)
        ],
    )
    return FlaskCustomer.objects.all()


def populate_flask_addresses(customers):
    addresses = []
    for _ in range(0, customers.count() * 2):
        address = FlaskAddress(
            street=fake.street_address(), city=fake.city(), country=fake.country(), zip_code=fake.postcode()
        )
        addresses.append(address)
    FlaskAddress.objects.bulk_create(addresses)
    addresses = FlaskAddress.objects.all()

    customers_addresses = []
    for address in addresses:
        known_customer = set()
        for _ in range(1, random.randint(2, 4)):
            customer = random.choices(customers)[0]
            if customer not in known_customer:
                known_customer.add(customer)
                customers_addresses.append(FlaskCustomersAddresses(address=address, customer=customer))
    FlaskCustomersAddresses.objects.bulk_create(customers_addresses)
    return addresses


def populate_orders(addresses):
    orders = []
    for address in addresses:
        o = FlaskOrder(
            amount=random.randint(10, 10000),
            created_at=fake.date_time_between_dates(datetime(2021, 1, 1), datetime.utcnow(), tzinfo=timezone.utc),
            customer=address.customers.all()[0],
            billing_address=address,
            delivering_address=address,
            status=random.choice(list(FlaskOrder.OrderStatus)),
        )
        orders.append(o)
    FlaskOrder.objects.bulk_create(orders)
    FlaskCart.objects.bulk_create(
        [FlaskCart(name=fake.language_name(), order_id=order.pk) for order in FlaskOrder.objects.all()]
    )
    return orders
