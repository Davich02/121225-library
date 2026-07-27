from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from django.http import HttpResponse, JsonResponse

from apps.library.models import Book
from apps.library.serializers import BookSerializer


# Create your views here.
def index(request):
    x = Book.objects.last()
    print(x)
    return HttpResponse("Hello, world. You're at the library index.")


@api_view(['GET', 'POST'])
def post_book(request):
    if request.method == 'POST':
        book = BookSerializer(data=request.data)

        if book.is_valid():
            book.save()
            return JsonResponse({"msg": "OK"}, status=200)
        else:
            return JsonResponse({"msg": book.errors}, status=400)

    if request.method == 'GET':
        return JsonResponse({"msg": "Hello"})
