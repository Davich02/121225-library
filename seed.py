import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()


from django.contrib.auth import get_user_model
from django.db import connection
from apps.library.models import Author, AuthorDetail, Book, Borrow, Library
from django.test.utils import CaptureQueriesContext
from django.db.models import Avg, Sum, Count, Max, Min, Subquery, OuterRef


User = get_user_model()


# with connection.cursor() as cursor:
#     cursor.execute('SELECT * FROM authors')
#     for author in cursor.fetchall():
#         print(author)
#     print('-' * 100)
#     cursor.execute('SELECT * FROM library_books')
#     for book in cursor.fetchall():
#         print(book)
#
# books = Book.objects.first()
# print(book)
#
# for q in connection.queries:
#     print(q)


class QueriesInfo:
    def __init__(self):
        self.__ctx = CaptureQueriesContext(connection)

    def __enter__(self):
        self.__ctx.__enter__()
        return self

    def __exit__(self, *args):
        self.__ctx.__exit__(*args)
        count = len(self.__ctx.captured_queries)
        print(f'Выполнено запросов: {count}')
        for q in self.__ctx.captured_queries[-5:]:
            print(f'   sql -> {q.get('sql')}\n  time -> {q.get('time')}\n{'-' * 20}')
        return False

#########
# Агрегация
########
def agg_ex_1():
    with QueriesInfo():
        # Первый и второй вариант идентичны по SQL запросам
        books = Book.objects.all()
        print(books.count())

        books = Book.objects.count()
        print(books)

        # Худший вариант получения количества объектов, так как работает на уровне Python
        books = Book.objects.all()
        print(len(books))


def agg_ex_2():
    with QueriesInfo():
        book = Book.objects.filter(title='Glass including scene upon last').first()
        print(book.rating_python)

        book = Book.objects.filter(title='Glass including scene upon last').first()
        print(book.rating_db)


def agg_ex_3():
    with QueriesInfo():
        result = Book.objects.aggregate(
            len=Count('id'),
            mean=Avg('page_count'),
            earlist=Min('published_at'),
            lates=Max('published_at'),
        )
        print(result)


def annotate_ex_1():
    with QueriesInfo():
        # books = Book.objects.annotate(borrow_count=Count('borrows'))
        # for book in books:
        #     print(book, book.borrow_count)

        books = Book.objects.annotate(borrow_count=Count('borrows')).values_list('title', 'borrow_count')
        for book in books:
            print(book)


def annotate_ex_2():
    with QueriesInfo():
        books = Book.objects.values('title').annotate(borrow_count=Count('borrows'))
        for book in books:
            print(book)


def order_by_ex_1():
    with QueriesInfo():
        books = Book.objects.order_by('author__first_name')
        for book in books:
            print(book)


def slice_ex_1():
    with QueriesInfo():
        books = Book.objects.all()[:5]
        print(books)

        books = Book.objects.all()[5:]
        print(books)

        books = Book.objects.all()[5:10]
        print(books)

def slice_ex_2():
    # Negative indexing is not supported
    with QueriesInfo():
        books = Book.objects.all()[::-1]
        print(books)

        books = Book.objects.all()[-5:]
        print(books)

        books = Book.objects.all()[-5:-10]
        print(books)

def slice_ex_3():
    with QueriesInfo():
        books = Book.objects.all()[2::2]
        print(books)


def sub_ex_1():
    with QueriesInfo():
        import math
        avg_page_count = Book.objects.aggregate(page_count=Avg('page_count'))['page_count']
        avg_page_count = math.ceil(avg_page_count)
        print(avg_page_count)
        books = Book.objects.filter(page_count__lt=avg_page_count)
        for book in books:
            print(book, book.page_count)


def sub_ex_2():
    with QueriesInfo():
        sub_query_ex2 = Subquery(
            Book.objects.filter(author=OuterRef('pk')).order_by('-published_at').values('published_at')[:1]
        )

        main_q = Author.objects.annotate(lates_book_date=sub_query_ex2).values_list('first_name', 'lates_book_date')

        for item in main_q:
            print(item)

def sub_ex_3():
    with QueriesInfo():
        active_borrows = Borrow.objects.filter(
            library=OuterRef('pk'), returned=False
        ).values('library').annotate(cnt=Count('id')).values('cnt')

        qs = Library.objects.annotate(
            active_borrows_count=Subquery(active_borrows)
        ).values('name', 'active_borrows_count')

        for item in qs:
            print(item)


def wrapper():
    from django.utils.timezone import now
    from django.db.models import ExpressionWrapper, F
    from django.db.models.fields import DurationField, IntegerField, FloatField
    from django.db.models.functions import ExtractYear
    from dateutil.relativedelta import relativedelta




    with QueriesInfo():
        # authors = Author.objects.annotate(
        #     age=(ExtractYear(now()) - ExtractYear(F('date_of_birth'))) / 24.0,
        #
        # )

        authors = Author.objects.annotate(
            age=ExpressionWrapper(
                ExtractYear(now()) - ExtractYear(F('date_of_birth')),
                output_field=IntegerField(),
            )
        )

        for author in authors:
            print(author, author.age)



if __name__ == '__main__':
    wrapper()
