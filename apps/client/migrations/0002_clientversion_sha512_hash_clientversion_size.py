# Generated by Django 4.2 on 2025-03-31 09:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientversion',
            name='sha512_hash',
            field=models.CharField(default='', max_length=128),
        ),
        migrations.AddField(
            model_name='clientversion',
            name='size',
            field=models.BigIntegerField(default=0),
        ),
    ]
