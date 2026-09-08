from __future__ import annotations

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from services.common.models import TimeStamped


class AccountManager(BaseUserManager):
    def create_user(self, email: str, password: str | None = None, **extra):
        if not email:
            raise ValueError("email required")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra):
        extra.setdefault("is_platform_admin", True)
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra)


class Account(TimeStamped, AbstractBaseUser, PermissionsMixin):
    """Global login identity. Tenant data is reached only through Memberships."""
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=32, blank=True)
    full_name = models.CharField(max_length=200)
    locale = models.CharField(max_length=8, default="ar")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_platform_admin = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]
    objects = AccountManager()

    class Meta:
        db_table = "identity_account"

    def __str__(self) -> str:
        return self.email
