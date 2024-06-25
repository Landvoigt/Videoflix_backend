import datetime

from django.db import models
from django.contrib.auth.models import User
from django.forms import ValidationError
from django.contrib.postgres.fields import ArrayField

class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="profiles", default=None, blank=True, null=True)
    name = models.CharField(max_length=40)
    description = models.CharField(max_length=700, blank=True, null=True)
    created_at = models.DateTimeField(default=datetime.date.today)
    avatar_id = models.SmallIntegerField()
    language = models.CharField(max_length=40, blank=True, null=True)
    view_list = ArrayField(models.IntegerField(), blank=True, default=list)
    liked_list = ArrayField(models.IntegerField(), blank=True, default=list)

    def clean(self):
        if self.user and self.user.profiles.count() >= 3:
            raise ValidationError("A user can have a maximum of 3 profiles.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name