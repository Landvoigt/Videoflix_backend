# Generated by Django 5.0.6 on 2024-08-31 13:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videostore', '0012_video_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='age',
            field=models.PositiveIntegerField(blank=True, choices=[(0, 'Ohne Altersbeschränkung'), (6, 'Ab 6 Jahren'), (12, 'Ab 12 Jahren'), (16, 'Ab 16 Jahren'), (18, 'Ab 18 Jahren')], null=True),
        ),
        migrations.AddField(
            model_name='video',
            name='resolution',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]