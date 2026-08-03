from django.urls import path
from .api_views import books_list_create, books_detail, BookDetailAPIView, BookListCreateAPIView

urlpatterns = [
    # path('books/', books_list_create, name='books_list_create'),
    # path('books/<uuid:pk>/', books_detail, name='books_detail'),

    path('books/', BookListCreateAPIView.as_view(), name='books_list_create'),
    path('books/<uuid:pk>/', BookDetailAPIView.as_view(), name='books_detail'),
]