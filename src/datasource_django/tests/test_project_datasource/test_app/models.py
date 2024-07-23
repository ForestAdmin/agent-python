from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models


class DjangoAuthUser(User):
    class Meta:
        proxy = True


class Book(models.Model):
    name = models.CharField(max_length=254)
    author = models.ForeignKey("Person", on_delete=models.CASCADE, related_name="books", null=True)
    price = models.DecimalField(decimal_places=2, max_digits=5)
    ratings = GenericRelation(
        "Rating",
        content_type_field="content_type",
        object_id_field="content_id",
        related_query_name="books",
    )
    tags = GenericRelation(
        "Tag",
        content_type_field="content_type",
        object_id_field="content_id",
        related_query_name="book",
    )


class Person(models.Model):
    first_name = models.CharField(max_length=254)
    last_name = models.CharField(max_length=254)
    birth_date = models.DateField()
    # Foreign key on proxy model
    auth_user = models.ForeignKey(DjangoAuthUser, on_delete=models.CASCADE, null=True)

    ratings = GenericRelation(
        "Rating",
        content_type_field="content_type",
        object_id_field="content_id",
        related_query_name="persons",
    )
    tags = GenericRelation(
        "Tag",
        content_type_field="content_type",
        object_id_field="content_id",
        related_query_name="person",
    )


class Rating(models.Model):
    RATE_CHOICES = [
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 4),
        (5, 5),
    ]
    comment = models.TextField(null=True)
    commenter = models.ForeignKey(Person, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATE_CHOICES)
    rated_at = models.DateTimeField()
    # polymorphic relation
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    content_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey("content_type", "content_id")


class Tag(models.Model):
    class Meta:
        unique_together = ("content_type", "content_id")

    tag = models.CharField(max_length=255)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    content_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey("content_type", "content_id")
