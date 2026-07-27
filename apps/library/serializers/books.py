from rest_framework import serializers

from apps.library.models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        exclude = ['created_at', 'updated_at', 'id']

