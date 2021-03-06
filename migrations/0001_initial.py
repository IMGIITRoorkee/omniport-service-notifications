# Generated by Django 2.2.3 on 2019-08-24 15:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('categories', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime_created', models.DateTimeField(auto_now_add=True)),
                ('datetime_modified', models.DateTimeField(auto_now=True)),
                ('template', models.CharField(db_index=True, max_length=500)),
                ('web_onclick_url', models.URLField(blank=True, null=True)),
                ('android_onclick_activity', models.CharField(blank=True, max_length=200, null=True)),
                ('ios_onclick_action', models.CharField(blank=True, max_length=200, null=True)),
                ('emailed', models.BooleanField(default=False)),
                ('is_personalised', models.BooleanField(default=False)),
                ('has_custom_users_target', models.BooleanField(default=False)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='categories.Category')),
            ],
            options={
                'ordering': ['-datetime_modified'],
                'unique_together': {('template', 'category')},
            },
        ),
    ]
