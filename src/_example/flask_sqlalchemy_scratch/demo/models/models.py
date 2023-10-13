import enum
import os

import sqlalchemy  # type: ignore
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, LargeBinary, String, func
from sqlalchemy.orm import relationship

sqlite_path = os.path.abspath(os.path.join(__file__, "..", "..", "..", "db.sql"))
SQLITE_URI = f"sqlite:///{sqlite_path}"


use_sqlalchemy_2 = sqlalchemy.__version__.split(".")[0] == "2"
if use_sqlalchemy_2:
    from sqlalchemy.orm import DeclarativeBase

    class Base(DeclarativeBase):
        pass

else:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import declarative_base

    engine = create_engine(SQLITE_URI, echo=False)
    Base = declarative_base()


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
    pk = Column(LargeBinary, primary_key=True)
    first_name = Column(String(254), nullable=False)
    last_name = Column(String(254), nullable=False)
    age = Column(Integer, nullable=True)
    birthday_date = Column(DateTime(timezone=True), default=func.now())
    addresses = relationship("Address", secondary="customers_addresses", back_populates="customers")
    is_vip = Column(Boolean, default=False)
    avatar = Column(LargeBinary, nullable=True)


class Order(Base):
    __tablename__ = "order"
    pk = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    amount = Column(Integer, nullable=False)
    customer = relationship("Customer", backref="orders")
    customer_id = Column(LargeBinary, ForeignKey("customer.pk"))
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
    customer_id = Column(LargeBinary, ForeignKey("customer.pk"), primary_key=True)
    address_id = Column(Integer, ForeignKey("address.pk"), primary_key=True)
