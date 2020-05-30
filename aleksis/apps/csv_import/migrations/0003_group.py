# Generated by Django 3.0.6 on 2020-05-27 17:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('csv_import', '0002_separator'),
    ]

    operations = [
        migrations.AddField(
            model_name='importtemplate',
            name='group',
            field=models.ForeignKey(blank=True, help_text='If imported objects are persons, they all will be members of this group after import.', null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.Group', verbose_name='Base group'),
        ),
    ]
