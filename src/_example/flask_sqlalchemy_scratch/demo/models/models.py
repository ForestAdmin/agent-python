import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, create_engine, func  # type: ignore
from sqlalchemy.orm import declarative_base, relationship

SQLITE_URI = "sqlite:///db.sql"
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
    id = Column(Integer, primary_key=True)
    street = Column(String(254), nullable=False)
    city = Column(String(254), nullable=False)
    country = Column(String(254), default="France", nullable=False)
    zip_code = Column(String(5), nullable=False)
    customers = relationship("Customer", secondary="customers_addresses", back_populates="addresses")


class Customer(Base):
    __tablename__ = "customer"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(254), nullable=False)
    last_name = Column(String(254), nullable=False)
    age = Column(Integer, nullable=True)
    birthday_date = Column(DateTime(timezone=True), default=func.now())
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
    cart = relationship("Cart", uselist=False, back_populates="order")


class Cart(Base):
    __tablename__ = "cart"
    id = Column(Integer, primary_key=True)

    name = Column(String(254), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    order_id = Column(Integer, ForeignKey("order.id"))
    order = relationship("Order", back_populates="cart", foreign_keys=[order_id])


class CustomersAddresses(Base):
    __tablename__ = "customers_addresses"
    customer_id = Column(Integer, ForeignKey("customer.id"), primary_key=True)
    address_id = Column(Integer, ForeignKey("address.id"), primary_key=True)
