from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.core.models import UUIDModel, Gender, age_validator
from apps.library.models import Library


class User(AbstractBaseUser, PermissionsMixin, UUIDModel):
    username = models.CharField(unique=True, max_length=50)
    email = models.EmailField(blank=True, null=True, unique=True)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    gender = models.CharField(max_length=1, choices=Gender.choices)
    birth_date = models.DateField(
        null=True, blank=True,
        validators=[age_validator],
        verbose_name=_('Date of Birth'),
    )
    avatar = models.ImageField(upload_to='avatars', null=True, blank=True)

    libraries = models.ManyToManyField(
        Library, verbose_name=_('Libraries'), blank=True, related_name='members'
    )

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    @property
    def age(self):
        today = timezone.now().date()
        if not self.birth_date:
            return None
        return (today.year - self.birth_date.year -
                ((today.month, today.day) < (self.birth_date.month, self.birth_date.day)))

    def __str__(self):
        return self.username