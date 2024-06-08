from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.db import models
from django.contrib.auth.hashers import make_password


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)

        username = self.generate_unique_username(
            extra_fields.get("first_name"), extra_fields.get("last_name")
        )

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

    def generate_unique_username(self, first_name, last_name):
        base_username = f"{first_name.lower()}{last_name.lower()}"
        username = base_username
        count = 1
        while self.model.objects.filter(username=username).exists():
            username = f"{base_username}{count}"
            count += 1
        return username


class CustomUser(AbstractUser):
    custom = models.CharField(max_length=500, default="", blank=True)
    phone = models.CharField(max_length=20, default="", blank=True)
    address = models.CharField(max_length=200, default="", blank=True)

    groups = models.ManyToManyField(
        Group,
        related_name="customuser_set",
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups",
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_permissions_set",
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
        related_query_name="customuser",
    )

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if not self.password.startswith("pbkdf2_sha256"):
            self.password = make_password(
                self.password
            )  # Hash the password same as in normal django user
        super().save(*args, **kwargs)
