# Generated by Django 5.2.3 on 2025-07-04 08:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurante_app', '0009_promocion'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedidodetalle',
            name='precio_unitario',
            field=models.IntegerField(default=0, help_text='Precio al momento de la compra, con descuentos aplicados.'),
        ),
    ]
