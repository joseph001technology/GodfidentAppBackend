from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base model with created_at and updated_at fields.

    All app models that track creation/update times should inherit from
    this instead of redeclaring the two fields individually, so the
    behavior (auto_now_add / auto_now) stays consistent everywhere.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True