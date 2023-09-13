import enum
import os

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, create_engine, func  # type: ignore
from sqlalchemy.orm import backref, declarative_base, relationship

sqlite_path = os.path.abspath(os.path.join(__file__, "..", "..", "..", "db.sql"))
SQLITE_URI = f"sqlite:///{sqlite_path}"
engine = create_engine(SQLITE_URI, echo=False)
Base = declarative_base(engine)
Base.metadata.bind = engine


class ORDER_STATUS(enum.Enum):
    PENDING = "Pending"
    DISPATCHED = "Dispatched"
    DELIVERED = "Delivered"
    REJECTED = "Rejected"


class Address(Base):
    __tablename__ = "address"
    pk = Column(Integer, primary_key=True)
    street = Column(String(254), nullable=False)
    street_number = Column(String(254), nullable=True)
    city = Column(String(254), nullable=False)
    country = Column(String(254), default="France", nullable=False)
    zip_code = Column(String(5), nullable=False, default="75009")
    customers = relationship("Customer", secondary="customers_addresses", back_populates="addresses")


class Customer(Base):
    __tablename__ = "customer"
    pk = Column(Integer, primary_key=True)
    first_name = Column(String(254), nullable=False)
    last_name = Column(String(254), nullable=False)
    age = Column(Integer, nullable=True)
    birthday_date = Column(DateTime(timezone=True), default=func.now())
    addresses = relationship("Address", secondary="customers_addresses", back_populates="customers")
    is_vip = Column(Boolean, default=False)
    # something_else = relationship("SomethingElse", backref="orders")
    # something_else_id = Column(Integer, ForeignKey("something_else.pk"))


class Order(Base):
    __tablename__ = "order"
    pk = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    amount = Column(Integer, nullable=False)
    customer = relationship("Customer", backref="orders")
    customer_id = Column(Integer, ForeignKey("customer.pk"))
    billing_address_id = Column(Integer, ForeignKey("address.pk"))
    billing_address = relationship("Address", foreign_keys=[billing_address_id], backref="billing_orders")
    delivering_address_id = Column(Integer, ForeignKey("address.pk"))
    delivering_address = relationship("Address", foreign_keys=[delivering_address_id], backref="delivering_orders")
    status = Column(Enum(ORDER_STATUS))

    cart = relationship("Cart", uselist=False, back_populates="order")


class Cart(Base):
    __tablename__ = "cart"
    pk = Column(Integer, primary_key=True)

    name = Column(String(254), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    order_id = Column(Integer, ForeignKey("order.pk"), nullable=True)
    order = relationship("Order", back_populates="cart")


class CustomersAddresses(Base):
    __tablename__ = "customers_addresses"
    customer_id = Column(Integer, ForeignKey("customer.pk"), primary_key=True)
    address_id = Column(Integer, ForeignKey("address.pk"), primary_key=True)


# class SomethingElse(Base):
#     __tablename__ = "something_else"
#     pk = Column(Integer, primary_key=True)
#     name = Column(String(254), nullable=False)
#     customer_id = Column(Integer, ForeignKey("customer.pk"))
#     customer = relationship("Customer", backref="elses")


# class SomeOneElse(Base):
#     __tablename__ = "someone_else"
#     prim_key = Column(Integer, primary_key=True)
#     name = Column(String(254), nullable=False)
#     something_elsse = relationship("SomethingElse", backref="someOne")
#     something_elsse_pk = Column(Integer, ForeignKey("something_else.pk"))
