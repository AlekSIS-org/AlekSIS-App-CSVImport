# Generated by Django 3.2.3 on 2021-05-23 12:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_fix_uniqueness_per_site'),
        ('csv_import', '0002_importjob'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='importtemplate',
            constraint=models.UniqueConstraint(fields=('site_id', 'name'), name='unique_template_name_per_site'),
        ),
    ]
