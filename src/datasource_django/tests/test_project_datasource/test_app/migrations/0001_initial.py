# Generated by Django 4.2.11 on 2024-07-26 07:55

import django.contrib.auth.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="Book",
            fields=[
                ("book_pk", models.BigAutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=254)),
                ("price", models.DecimalField(decimal_places=2, max_digits=5)),
            ],
        ),
        migrations.CreateModel(
            name="Person",
            fields=[
                ("person_pk", models.BigAutoField(primary_key=True, serialize=False)),
                ("first_name", models.CharField(max_length=254)),
                ("last_name", models.CharField(max_length=254)),
                ("birth_date", models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name="DjangoAuthUser",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("auth.user",),
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="Rating",
            fields=[
                ("rating_pk", models.BigAutoField(primary_key=True, serialize=False)),
                ("comment", models.TextField(null=True)),
                (
                    "rating",
                    models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]),
                ),
                ("rated_at", models.DateTimeField()),
                ("content_id", models.PositiveIntegerField(null=True)),
                (
                    "book",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="test_app.book"),
                ),
                (
                    "commenter",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="test_app.person",
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.contenttype",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="person",
            name="auth_user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="test_app.djangoauthuser",
            ),
        ),
        migrations.AddField(
            model_name="book",
            name="author",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="books",
                to="test_app.person",
            ),
        ),
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("tag_pk", models.BigAutoField(primary_key=True, serialize=False)),
                ("tag", models.CharField(max_length=255)),
                ("content_id", models.PositiveIntegerField(null=True)),
                (
                    "content_type",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.contenttype",
                    ),
                ),
            ],
            options={
                "unique_together": {("content_type", "content_id")},
            },
        ),
    ]
