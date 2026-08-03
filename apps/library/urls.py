from django.urls import path
from .views import books, books_2025, books_2026

app_name = 'library'

urlpatterns = [
    path('books/', books, name='books'),
    path('books/2025/', books_2025, name='books_2025'),
    path('books/2026/', books_2026, name='books_2026'),
]