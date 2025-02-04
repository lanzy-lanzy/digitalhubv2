# Generated by Django 5.1.5 on 2025-02-04 04:25

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scholar', '0004_remove_paper_introduction_remove_paper_pdf_file_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='paper',
            name='viewers',
            field=models.ManyToManyField(blank=True, related_name='viewed_papers', to=settings.AUTH_USER_MODEL),
        ),
    ]
