"""
apps/users/models.py

Custom User model.

Uses UUID as primary key instead of the default integer ID.
All external-facing user identifiers are UUIDs — they reveal no sequence information.

AUTH_USER_MODEL = "users.User" is set in config/settings/base.py.
"""
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Project user model.

    Extends Django's AbstractUser with:
    - UUID primary key
    - Audit timestamps (created_at, updated_at)

    The default username/email/password fields from AbstractUser are retained.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.email or self.username
