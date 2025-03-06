# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class FlaskAddress(models.Model):
    id = models.AutoField(primary_key=True, db_column="pk")
    street = models.CharField(max_length=255)
    street_number = models.CharField(max_length=2, blank=True, null=True)
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    zip_code = models.CharField(max_length=5)
    # customers = models.ManyToManyField("FlaskCustomer", through="FlaskCustomersAddresses")

    class Meta:
        # managed = False
        db_table = "address"


class FlaskCustomer(models.Model):
    id = models.UUIDField(primary_key=True, db_column="pk")
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    birthday_date = models.DateTimeField(blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    is_vip = models.BooleanField(blank=True, null=True)
    avatar = models.BinaryField(blank=True, null=True, editable=True)
    addresses = models.ManyToManyField("FlaskAddress", through="FlaskCustomersAddresses", related_name="customers")

    class Meta:
        # managed = False
        db_table = "customer"


class FlaskCustomersAddresses(models.Model):
    customer = models.ForeignKey(FlaskCustomer, models.DO_NOTHING)
    address = models.ForeignKey(FlaskAddress, models.DO_NOTHING)

    class Meta:
        # managed = False
        db_table = "customers_addresses"


class FlaskOrder(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING = ("PENDING", "Pending")
        DISPATCHED = ("DISPATCHED", "Dispatched")
        DELIVERED = ("DELIVERED", "Delivered")
        REJECTED = ("REJECTED", "Rejected")

    id = models.AutoField(primary_key=True, db_column="pk")
    created_at = models.DateTimeField(blank=True, null=True)
    amount = models.IntegerField()
    customer = models.ForeignKey(FlaskCustomer, models.DO_NOTHING, blank=True, null=True)
    billing_address = models.ForeignKey(FlaskAddress, models.DO_NOTHING, blank=True, null=True)
    delivering_address = models.ForeignKey(
        FlaskAddress, models.DO_NOTHING, related_name="order_delivering_address_set", blank=True, null=True
    )
    status = models.CharField(max_length=10, choices=OrderStatus.choices)

    class Meta:
        # managed = False
        db_table = "order"


class FlaskCart(models.Model):
    id = models.AutoField(primary_key=True, db_column="pk")
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)
    order = models.ForeignKey("FlaskOrder", models.DO_NOTHING, blank=True, null=True)

    class Meta:
        # managed = False
        db_table = "cart"
