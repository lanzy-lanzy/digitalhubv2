# Generated by Django 5.1.7 on 2025-03-29 07:49

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scholar', '0008_paper_program'),
    ]

    operations = [
        migrations.AddField(
            model_name='borrow',
            name='borrow_reason',
            field=models.TextField(blank=True, help_text='Reason for borrowing this paper', null=True),
        ),
        migrations.AddField(
            model_name='borrow',
            name='request_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='borrow',
            name='borrow_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
