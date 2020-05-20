# Generated by Django 3.0.6 on 2020-05-17 11:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("csv_import", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="importtemplate",
            name="separator",
            field=models.CharField(
                choices=[(",", ","), (";", ";"), ("\\s+", "Whitespace"), ("\t", "Tab")],
                default=",",
                max_length=255,
                verbose_name="CSV separator",
            ),
        ),
        migrations.AlterField(
            model_name="importtemplatefield",
            name="field_type",
            field=models.CharField(
                choices=[
                    ("unique_reference", "Unique reference"),
                    ("is_active", "Is active? (0/1)"),
                    ("first_name", "First name"),
                    ("last_name", "Last name"),
                    ("additional_name", "Additional name"),
                    ("short_name", "Short name"),
                    ("email", "Email"),
                    ("date_of_birth", "Date of birth"),
                    ("sex", "Sex"),
                    ("street", "Street"),
                    ("housenumber", "Housenumber"),
                    ("postal_code", "Postal code"),
                    ("place", "Place"),
                    ("phone_number", "Phone number"),
                    ("mobile_number", "Mobile number"),
                    ("ignore", "Ignore data in this field"),
                    (
                        "is_active_schild_nrw_students",
                        "Is active? (SchILD-NRW: students)",
                    ),
                    ("subjects", "Comma-separated list of subjects"),
                ],
                max_length=255,
                verbose_name="Field type",
            ),
        ),
    ]
