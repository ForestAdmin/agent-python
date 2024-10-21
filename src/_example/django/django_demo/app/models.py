from datetime import date

# from django.db.models.functions import Concat
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models

# uncomment this to reenable "other" database
# from app.flask_models import *  # noqa:F401,F403


"""
checklist:
* data types:
    * https://docs.djangoproject.com/en/4.2/ref/models/fields/#model-field-types /
        https://github.com/django/django/blob/main/django/db/models/fields/__init__.py
    * CharField / TextField
    * IntegerField / FloatField / DecimalField / BigIntegerField(IntegerField) / SmallIntegerField(IntegerField) /
        PositiveBigIntegerField(BigIntegerField) / PositiveIntegerField(IntegerField) /
        PositiveSmallIntegerField(SmallIntegerField)
    * AutoField(IntegerField) / BigAutoField(BigIntegerField) / SmallAutoField(SmallIntegerField)
    * BooleanField(already in django user) / NullBooleanField(BooleanField)
    * BinaryField / FileField / FilePathField / image(FileField)
    * DateField / DateTimeField(DateField) / TimeField / DurationField??
    * EmailField(CharField)
    * IPAddressField / GenericIPAddressField
    * JSONField
    * SlugField(CharField)
    * URLField(CharField)
    * UUIDField
    * CommaSeparatedIntegerField(CharField) ???
* field options
    * db_column
    * primary key
    * null / blank
    * max_length
    * default value
    * choices
    * verbose name ??
    * validators
* relations
    * oneToOne
    * oneToMany
    * ManyToOne
    * ManyToMany: with explicit/implicit join table
* models inheritance
    * abstract models
    * proxy models
* custom table name
* constraints: on one field only, constraints for multi fields not handle ? (unique=True, vs unique_together)
"""


class AutoUpdatedCreatedAt(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Address(models.Model):
    # pk = models.BigAutoField(primary_key=True)
    street = models.CharField(max_length=254)
    number = models.CharField(max_length=254, db_column="street_number")
    city = models.CharField(max_length=254)
    country = models.CharField(max_length=254, default="France")
    zip_code = models.CharField(max_length=5, default="75009")

    # test with django 5 ; if enable, don't forget to make migration and migrate
    # full_text_address = models.GeneratedField(
    #     expression=Concat(
    #         models.F("number"),
    #         models.Value(" "),
    #         models.F("street"),
    #         models.Value(" "),
    #         models.F("zip_code"),
    #         models.Value(" "),
    #         models.F("city"),
    #         models.Value(" "),
    #         models.F("country"),
    #     ),
    #     output_field=models.TextField(),
    #     db_persist=False,
    # )

    customers = models.ManyToManyField(
        "Customer", related_name="addresses", through="CustomerAddress", through_fields=("address", "customer")
    )


class CustomerAddress(models.Model):
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    customer = models.ForeignKey("Customer", on_delete=models.CASCADE)


class Customer(AutoUpdatedCreatedAt):
    # pk = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=254)
    last_name = models.CharField(max_length=254)
    birthday_date = models.DateField(default=date.today)
    # age = should_be computed
    # addresses = models.ManyToManyField(Address, related_name="customers")
    is_vip = models.BooleanField(default=False)
    avatar = models.BinaryField(null=True, blank=True, editable=True)

    blocked_customer = models.ManyToManyField("self", blank=True, related_name="block_by_users", symmetrical=False)

    tags = GenericRelation(
        "Tag",
        content_type_field="tagged_item_type",
        object_id_field="tagged_item_id",
        related_query_name="customers",
    )


class Order(AutoUpdatedCreatedAt):
    class OrderStatus(models.TextChoices):
        PENDING = ("PENDING", "Pending")
        DISPATCHED = ("DISPATCHED", "Dispatched")
        DELIVERED = ("DELIVERED", "Delivered")
        REJECTED = ("REJECTED", "Rejected")

    # pk = models.BigAutoField(primary_key=True)
    amount = models.DecimalField(decimal_places=2, max_digits=15)
    customer = models.ForeignKey(Customer, related_name="orders", on_delete=models.CASCADE, null=True)
    billing_address = models.ForeignKey(Address, related_name="billing_orders", on_delete=models.CASCADE)
    delivering_address = models.ForeignKey(Address, related_name="delivering_orders", on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=OrderStatus.choices)
    ordered_at = models.DateTimeField(null=True)
    # cart

    tags = GenericRelation(
        "Tag",
        content_type_field="tagged_item_type",
        object_id_field="tagged_item_id",
        related_query_name="orders",
    )


class Cart(models.Model):
    # pk = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=254)
    created_at = models.DateTimeField(auto_now_add=True)

    order = models.OneToOneField(Order, on_delete=models.CASCADE, null=True)


class ExtendedCart(models.Model):
    cart = models.OneToOneField(Cart, primary_key=True, on_delete=models.CASCADE)
    color = models.CharField(max_length=20)
    discount = models.OneToOneField("DiscountCart", on_delete=models.CASCADE, null=True)


class DiscountCart(models.Model):
    discount = models.FloatField()


class Tag(models.Model):
    # comment this to set the reverse relations to oneToMany
    class Meta:
        unique_together = ("tagged_item_type", "tagged_item_id")

    tagged_item_id = models.IntegerField()
    tagged_item_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    tagged_item = GenericForeignKey("tagged_item_type", "tagged_item_id")
    tag = models.CharField(max_length=255)
