# Generated by Django 3.0.6 on 2020-05-12 17:45

import django.contrib.postgres.fields.jsonb
import django.contrib.sites.managers
import django.db.models.deletion
from django.db import migrations, models

import aleksis.apps.csv_import.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("sites", "0002_alter_domain_unique"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="ImportTemplate",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "extended_data",
                    django.contrib.postgres.fields.jsonb.JSONField(
                        default=dict, editable=False
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=255, unique=True, verbose_name="Name"),
                ),
                ("verbose_name", models.CharField(max_length=255, verbose_name="Name")),
                (
                    "has_header_row",
                    models.BooleanField(
                        default=True, verbose_name="Has the CSV file a own header row?"
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        limit_choices_to=aleksis.apps.csv_import.models.get_allowed_content_types_query,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.ContentType",
                        verbose_name="Content type",
                    ),
                ),
                (
                    "site",
                    models.ForeignKey(
                        default=1,
                        editable=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="sites.Site",
                    ),
                ),
            ],
            options={
                "verbose_name": "Import template",
                "verbose_name_plural": "Import templates",
                "ordering": ["name"],
            },
            managers=[("objects", django.contrib.sites.managers.CurrentSiteManager()),],
        ),
        migrations.CreateModel(
            name="ImportTemplateField",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "extended_data",
                    django.contrib.postgres.fields.jsonb.JSONField(
                        default=dict, editable=False
                    ),
                ),
                ("index", models.IntegerField(verbose_name="Index")),
                (
                    "field_type",
                    models.CharField(
                        choices=[
                            ("is_active", "Is active?"),
                            ("first_name", "First name"),
                            ("last_name", "Last name"),
                        ],
                        max_length=255,
                        verbose_name="Field type",
                    ),
                ),
                (
                    "site",
                    models.ForeignKey(
                        default=1,
                        editable=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="sites.Site",
                    ),
                ),
                (
                    "template",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="fields",
                        to="csv_import.ImportTemplate",
                        verbose_name="Import template",
                    ),
                ),
            ],
            options={
                "verbose_name": "Import template field",
                "verbose_name_plural": "Import template fields",
                "ordering": ["template", "index"],
                "unique_together": {("template", "index")},
            },
            managers=[("objects", django.contrib.sites.managers.CurrentSiteManager()),],
        ),
    ]
