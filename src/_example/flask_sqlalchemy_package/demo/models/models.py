import enum

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, LargeBinary, String, Uuid, func
from sqlalchemy.orm import relationship

db = SQLAlchemy()


class ORDER_STATUS(enum.Enum):
    PENDING = "Pending"
    DISPATCHED = "Dispatched"
    DELIVERED = "Delivered"
    REJECTED = "Rejected"


class Address(db.Model):
    __tablename__ = "address"
    pk = Column(Integer, primary_key=True)
    street = Column(String(254), nullable=False)
    street_number = Column(String(254), nullable=True)
    city = Column(String(254), nullable=False)
    country = Column(String(254), default="France", nullable=False)
    zip_code = Column(String(5), nullable=False, default="75009")
    customers = relationship("Customer", secondary="customers_addresses", back_populates="addresses")


class Customer(db.Model):
    __tablename__ = "customer"
    pk = Column(Uuid, primary_key=True)
    first_name = Column(String(254), nullable=False)
    last_name = Column(String(254), nullable=False)
    birthday_date = Column(DateTime(timezone=True), default=func.now())
    age = Column(Integer, nullable=True)
    addresses = relationship("Address", secondary="customers_addresses", back_populates="customers")
    is_vip = Column(Boolean, default=False)
    avatar = Column(LargeBinary, nullable=True)


class Order(db.Model):
    __tablename__ = "order"
    pk = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    amount = Column(Integer, nullable=False)
    customer = relationship("Customer", backref="orders")
    customer_id = Column(Uuid, ForeignKey("customer.pk"))
    billing_address_id = Column(Integer, ForeignKey("address.pk"))
    billing_address = relationship("Address", foreign_keys=[billing_address_id], backref="billing_orders")
    delivering_address_id = Column(Integer, ForeignKey("address.pk"))
    delivering_address = relationship("Address", foreign_keys=[delivering_address_id], backref="delivering_orders")
    status = Column(Enum(ORDER_STATUS))
    cart = relationship("Cart", uselist=False, backref="order")


class Cart(db.Model):
    __tablename__ = "cart"
    pk = Column(Integer, primary_key=True)

    name = Column(String(254), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    order_id = Column(Integer, ForeignKey("order.pk"))


class CustomersAddresses(db.Model):
    __tablename__ = "customers_addresses"
    customer_id = Column(Uuid, ForeignKey("customer.pk"), primary_key=True)
    address_id = Column(Integer, ForeignKey("address.pk"), primary_key=True)
