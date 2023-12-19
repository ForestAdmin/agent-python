from django.contrib.auth.models import User
from django.db import models


class DjangoAuthUser(User):
    class Meta:
        proxy = True


class Book(models.Model):
    name = models.CharField(max_length=254)
    author = models.ForeignKey("Person", on_delete=models.CASCADE, related_name="books")


class Person(models.Model):
    first_name = models.CharField(max_length=254)
    last_name = models.CharField(max_length=254)
    birth_date = models.DateField()
    # Foreign key on proxy model
    auth_user = models.ForeignKey(DjangoAuthUser, on_delete=models.CASCADE, null=True)


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
    rated_at = models.DateField()
