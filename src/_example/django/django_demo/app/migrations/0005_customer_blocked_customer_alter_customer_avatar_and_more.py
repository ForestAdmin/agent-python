# Generated by Django 4.2 on 2024-01-18 16:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0004_discountcart_extendedcart_discount"),
    ]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="blocked_customer",
            field=models.ManyToManyField(
                blank=True, related_name="block_by_customers", to="app.customer"
            ),
        ),
        migrations.AlterField(
            model_name="customer",
            name="avatar",
            field=models.BinaryField(blank=True, editable=True, null=True),
        ),
        migrations.AlterField(
            model_name="flaskcustomer",
            name="avatar",
            field=models.BinaryField(blank=True, editable=True, null=True),
        ),
    ]
