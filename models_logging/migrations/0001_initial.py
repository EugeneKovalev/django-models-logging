# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-12 11:01
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.LOGGING_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Changes',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, db_index=True, help_text='The date and time this changes was.', verbose_name='Date created')),
                ('comment', models.TextField(help_text='A text comment on this changes.', verbose_name='Comment')),
                ('object_id', models.CharField(help_text='Primary key of the model under version control.', max_length=191)),
                ('db', models.CharField(help_text='The database the model under version control is stored in.', max_length=191)),
                ('serialized_data', models.TextField(blank=True, help_text='The serialized form of this version of the model.', null=True)),
                ('object_repr', models.TextField(help_text='A string representation of the object.')),
                ('action', models.CharField(help_text='added|changed|deleted', max_length=7, verbose_name='Action')),
                ('content_type', models.ForeignKey(help_text='Content type of the model under version control.', on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
            ],
            options={
                'verbose_name_plural': 'All changes',
                'ordering': ('-pk',),
                'verbose_name': 'Changes of object',
            },
        ),
        migrations.CreateModel(
            name='Revision',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, db_index=True, help_text='The date and time this revision was created.', verbose_name='date created')),
                ('comment', models.TextField(blank=True, help_text='A text comment on this revision.', null=True, verbose_name='comment')),
            ],
            options={
                'verbose_name_plural': 'Revisions',
                'ordering': ('-pk',),
                'verbose_name': 'Revision',
            },
        ),
        migrations.AddField(
            model_name='changes',
            name='revision',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='models_logging.Revision', verbose_name='to revision'),
        ),
        migrations.AddField(
            model_name='changes',
            name='user',
            field=models.ForeignKey(
                blank=True,
                help_text='A user who performed a change',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.LOGGING_USER_MODEL,
                verbose_name='User'
            )
        ),
    ]
