from django.utils import timezone

from rest_framework import serializers

from apps.library.models import Book, Library
from .authors import AuthorSerializer


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        exclude = ['created_at', 'updated_at', 'id']


class BookCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            'title',
            'author',
            'published_at',
            'genre',
            'page_count',
            'category',
            'publisher',
            'libraries',
            'description',
            'photo'
        ]

    def validate_published_at(self, value):
        if value > timezone.now():
            raise serializers.ValidationError('Published at is in the future')
        return value

    def update(self, instance, validated_data):
        if 'title' in validated_data:
            validated_data['title'] = validated_data['title'].strip().upper()

        return super().update(instance, validated_data)



class BookListSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    author_full = AuthorSerializer(source='author')
    libraries = serializers.SlugRelatedField(many=True, slug_field='slug', queryset=Library.objects.all())

    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'author',
            'author_full',
            'published_at',
            'genre',
            'page_count',
            'category',
            'publisher',
            'libraries',
            'description',
            'photo'
        ]
