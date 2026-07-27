import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()


from django.contrib.auth import get_user_model
from apps.library.models import Author, AuthorDetail, Book


User = get_user_model()