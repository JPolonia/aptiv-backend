# Generated by Django 2.0.13 on 2019-03-25 12:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_auto_20190325_1138'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aptivvalidate',
            name='output',
            field=models.TextField(blank=True, null=True),
        ),
    ]