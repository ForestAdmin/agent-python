# Generated by Django 4.2.7 on 2023-11-28 15:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="FlaskAddress",
            fields=[
                (
                    "id",
                    models.AutoField(db_column="pk", primary_key=True, serialize=False),
                ),
                ("street", models.CharField(max_length=255)),
                (
                    "street_number",
                    models.CharField(blank=True, max_length=2, null=True),
                ),
                ("city", models.CharField(max_length=255)),
                ("country", models.CharField(max_length=255)),
                ("zip_code", models.CharField(max_length=5)),
            ],
            options={
                "db_table": "address",
            },
        ),
        migrations.CreateModel(
            name="FlaskCustomer",
            fields=[
                (
                    "id",
                    models.BinaryField(
                        db_column="pk", primary_key=True, serialize=False
                    ),
                ),
                ("first_name", models.CharField(max_length=255)),
                ("last_name", models.CharField(max_length=255)),
                ("birthday_date", models.DateTimeField(blank=True, null=True)),
                ("age", models.IntegerField(blank=True, null=True)),
                ("is_vip", models.BooleanField(blank=True, null=True)),
                ("avatar", models.BinaryField(blank=True, null=True)),
            ],
            options={
                "db_table": "customer",
            },
        ),
        migrations.CreateModel(
            name="FlaskOrder",
            fields=[
                (
                    "id",
                    models.AutoField(db_column="pk", primary_key=True, serialize=False),
                ),
                ("created_at", models.DateTimeField(blank=True, null=True)),
                ("amount", models.IntegerField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("DISPATCHED", "Dispatched"),
                            ("DELIVERED", "Delivered"),
                            ("REJECTED", "Rejected"),
                        ],
                        max_length=10,
                    ),
                ),
                (
                    "billing_address",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="app.flaskaddress",
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="app.flaskcustomer",
                    ),
                ),
                (
                    "delivering_address",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="order_delivering_address_set",
                        to="app.flaskaddress",
                    ),
                ),
            ],
            options={
                "db_table": "order",
            },
        ),
        migrations.CreateModel(
            name="FlaskCustomersAddresses",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "address",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="app.flaskaddress",
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="app.flaskcustomer",
                    ),
                ),
            ],
            options={
                "db_table": "customers_addresses",
            },
        ),
        migrations.AddField(
            model_name="flaskcustomer",
            name="addresses",
            field=models.ManyToManyField(
                related_name="customers",
                through="app.FlaskCustomersAddresses",
                to="app.flaskaddress",
            ),
        ),
        migrations.CreateModel(
            name="FlaskCart",
            fields=[
                (
                    "id",
                    models.AutoField(db_column="pk", primary_key=True, serialize=False),
                ),
                ("name", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(blank=True, null=True)),
                (
                    "order",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="app.flaskorder",
                    ),
                ),
            ],
            options={
                "db_table": "cart",
            },
        ),
    ]