# Generated by Django 2.0.13 on 2019-03-24 19:13

import aptiv_backend.core.models.excel
import aptiv_backend.core.models.pdf
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AptivValidate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('output', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Excel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('excel_file', models.FileField(upload_to=aptiv_backend.core.models.excel.import_file_path)),
                ('rev_letter', models.CharField(blank=True, max_length=10, null=True)),
                ('compare_id', models.IntegerField(blank=True, null=True)),
                ('compare_data', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Pdf',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pdf_file', models.FileField(upload_to=aptiv_backend.core.models.pdf.import_file_path)),
                ('rev_letter', models.CharField(blank=True, max_length=10, null=True)),
                ('compare_id', models.IntegerField(blank=True, null=True)),
                ('compare_data', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='aptivvalidate',
            name='excel',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Excel'),
        ),
        migrations.AddField(
            model_name='aptivvalidate',
            name='pdf',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Pdf'),
        ),
    ]
