import uuid
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Gender(models.TextChoices):
    MALE = 'M', _('Male')
    FEMALE = 'F', _('Female')
    OTHER = 'O', _('Other')


def age_validator(value):
    today = timezone.now().date()
    if value > today:
        raise ValidationError('You are not born yet')

    age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    if not 6 <= age <= 120:
        raise ValidationError('Your age must be between 6 and 120!')
