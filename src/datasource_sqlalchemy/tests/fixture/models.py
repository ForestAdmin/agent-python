import enum
import json
import os
from datetime import date, datetime

import sqlalchemy  # type: ignore
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, create_engine, func, types
from sqlalchemy.orm import Session, relationship, validates

use_sqlalchemy_2 = sqlalchemy.__version__.split(".")[0] == "2"
fixtures_dir = os.path.abspath(os.path.join(__file__, ".."))

# to import/export json as fixtures
# https://gist.github.com/shazow/789309
convert_types = {
    types.LargeBinary: (lambda o: o.encode("hex"), lambda s: s.decode("hex")),
    types.DateTime: (lambda o: o.strftime("%Y-%m-%d %H:%M:%S"), lambda s: datetime.strptime(s, "%Y-%m-%d %H:%M:%S")),
    types.Date: (lambda o: o.strftime("%Y-%m-%d"), lambda s: date.strptime(s, "%Y-%m-%d")),
}


class _Base(object):
    def __export__(self):
        d = {}
        for col in self.__table__.columns:
            encode, decode = convert_types.get(col.type.__class__, (lambda v: v, lambda v: v))
            d[col.name] = encode(getattr(self, col.name))

        return d

    @classmethod
    def __import__(cls, d):
        params = {}
        for k, v in d.items():
            col = cls.__table__.columns.get(k)
            if col is None:
                continue

            encode, decode = convert_types.get(col.type.__class__, (lambda v: v, lambda v: v))
            params[str(k)] = decode(v)

        return cls(**params)


if use_sqlalchemy_2:
    from sqlalchemy.orm import DeclarativeBase

    class Base(DeclarativeBase, _Base):
        pass

else:
    from sqlalchemy.orm import declarative_base

    Base = declarative_base(cls=_Base)


def get_models_base(db_file_name):
    test_db_path = os.path.abspath(os.path.join(__file__, "..", "..", "..", "..", "..", f"{db_file_name}.sql"))
    engine = create_engine(f"sqlite:///{test_db_path}", echo=False)
    Base.metadata.bind = engine
    Base.metadata.file_path = test_db_path
    return Base


class ORDER_STATUS(str, enum.Enum):
    PENDING = "Pending"
    DISPATCHED = "Dispatched"
    DELIVERED = "Delivered"
    REJECTED = "Rejected"


class Address(Base):
    __tablename__ = "address"
    id = Column(Integer, primary_key=True)
    street = Column(String(254), nullable=False)
    city = Column(String(254), nullable=False)
    country = Column(String(254), nullable=False)
    zip_code = Column(String(5), nullable=False)
    customers = relationship("Customer", secondary="customers_addresses", back_populates="addresses")

    @validates("zip_code")
    def validate_zip_code(self, key, zip_code):
        try:
            int(zip_code)
        except ValueError:
            raise TypeError("zip_code must be 5 numbers string")

        if len(str(zip_code)) != 5:
            raise TypeError("zip_code must be 5 numbers string")

        return str(zip_code)


class Customer(Base):
    __tablename__ = "customer"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(254), nullable=False)
    last_name = Column(String(254), nullable=False)
    age = Column(Integer, nullable=True)
    addresses = relationship("Address", secondary="customers_addresses", back_populates="customers")


class Order(Base):
    __tablename__ = "order"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    amount = Column(Integer, nullable=False)
    customer = relationship("Customer", backref="orders")
    customer_id = Column(Integer, ForeignKey("customer.id"))
    billing_address_id = Column(Integer, ForeignKey("address.id"))
    billing_address = relationship("Address", foreign_keys=[billing_address_id], backref="billing_orders")
    delivering_address_id = Column(Integer, ForeignKey("address.id"))
    delivering_address = relationship("Address", foreign_keys=[delivering_address_id], backref="delivering_orders")
    status = Column(Enum(ORDER_STATUS))


class CustomersAddresses(Base):
    __tablename__ = "customers_addresses"
    customer_id = Column(Integer, ForeignKey("customer.id"), primary_key=True)
    address_id = Column(Integer, ForeignKey("address.id"), primary_key=True)


def load_fixtures(base):
    with open(os.path.join(fixtures_dir, "addresses.json"), "r") as fin:
        data = json.load(fin)
        addresses = [Address.__import__(d) for d in data]

    with open(os.path.join(fixtures_dir, "customers.json"), "r") as fin:
        data = json.load(fin)
        customers = [Customer.__import__(d) for d in data]

    with open(os.path.join(fixtures_dir, "customers_addresses.json"), "r") as fin:
        data = json.load(fin)
        customers_addresses = [CustomersAddresses.__import__(d) for d in data]

    with open(os.path.join(fixtures_dir, "orders.json"), "r") as fin:
        data = json.load(fin)
        orders = [Order.__import__(d) for d in data]

    with Session(base.metadata.bind) as session:
        session.bulk_save_objects(addresses)
        session.bulk_save_objects(customers)
        session.bulk_save_objects(customers_addresses)
        session.bulk_save_objects(orders)
        session.commit()


def create_test_database(base):
    base.metadata.create_all(base.metadata.bind)
