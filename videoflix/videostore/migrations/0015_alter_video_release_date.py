# Generated by Django 5.0.6 on 2024-09-05 18:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videostore', '0014_video_release_date_alter_video_category_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='video',
            name='release_date',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
