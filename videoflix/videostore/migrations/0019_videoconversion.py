# Generated by Django 5.0.6 on 2024-10-14 11:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videostore', '0018_video_video_duration'),
    ]

    operations = [
        migrations.CreateModel(
            name='VideoConversion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('video', models.FileField(upload_to='videos/')),
                ('job_id', models.CharField(blank=True, max_length=100, null=True)),
                ('progress', models.IntegerField(default=0)),
            ],
        ),
    ]
