# Generated by Django 3.2.3 on 2021-05-19 18:41

import django.contrib.sites.managers
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        ('core', '0017_dashboardwidget_broken'),
        ('csv_import', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImportJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('extended_data', models.JSONField(default=dict, editable=False)),
                ('data_file', models.FileField(upload_to='csv_import/')),
                ('school_term', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='import_jobs', to='core.schoolterm', verbose_name='School term')),
                ('site', models.ForeignKey(default=1, editable=False, on_delete=django.db.models.deletion.CASCADE, to='sites.site')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='import_jobs', to='csv_import.importtemplate', verbose_name='Import template')),
            ],
            options={
                'verbose_name': 'Import job',
                'verbose_name_plural': 'Import jobs',
            },
            managers=[
                ('objects', django.contrib.sites.managers.CurrentSiteManager()),
            ],
        ),
    ]
