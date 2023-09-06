import enum

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

db = SQLAlchemy()


class ORDER_STATUS(enum.Enum):
    PENDING = "Pending"
    DISPATCHED = "Dispatched"
    DELIVERED = "Delivered"
    REJECTED = "Rejected"


class Address(db.Model):
    __tablename__ = "address"
    id = Column(Integer, primary_key=True)
    street = Column(String(254), nullable=False)
    city = Column(String(254), nullable=False)
    country = Column(String(254), default="France", nullable=False)
    zip_code = Column(String(5), nullable=False, default="75009")
    customers = relationship("Customer", secondary="customers_addresses", back_populates="addresses")


class Customer(db.Model):
    __tablename__ = "customer"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(254), nullable=False)
    last_name = Column(String(254), nullable=False)
    birthday_date = Column(DateTime(timezone=True), default=func.now())
    age = Column(Integer, nullable=True)
    addresses = relationship("Address", secondary="customers_addresses", back_populates="customers")
    is_vip = Column(Boolean, default=False)


class Order(db.Model):
    __tablename__ = "order"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    amount = Column(Integer, nullable=False)
    customer = relationship("Customer", backref="orders")
    customer_id = Column(Integer, ForeignKey("customer.id"))
    billing_address_id = Column(Integer, ForeignKey("address.id"))
    billing_address = relationship("Address", foreign_keys=[billing_address_id], backref="billing_orders")
    delivering_address_id = Column(Integer, ForeignKey("address.id"))
    delivering_address = relationship("Address", foreign_keys=[delivering_address_id], backref="delivering_orders")
    status = Column(Enum(ORDER_STATUS))
    cart = relationship("Cart", uselist=False, backref="order")


class Cart(db.Model):
    __tablename__ = "cart"
    id = Column(Integer, primary_key=True)

    name = Column(String(254), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    order_id = Column(Integer, ForeignKey("order.id"))


class CustomersAddresses(db.Model):
    __tablename__ = "customers_addresses"
    customer_id = Column(Integer, ForeignKey("customer.id"), primary_key=True)
    address_id = Column(Integer, ForeignKey("address.id"), primary_key=True)
