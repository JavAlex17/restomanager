# Generated by Django 5.2.3 on 2025-06-12 07:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurante_app', '0005_alter_producto_categoria'),
    ]

    operations = [
        migrations.AlterField(
            model_name='producto',
            name='nombre',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
