from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import redirect


def books(request):
    return render(request, 'books.html')


def books_2025(request):
    return HttpResponse('books 2025')


def books_2026(request):
    return redirect('library:books_2025')