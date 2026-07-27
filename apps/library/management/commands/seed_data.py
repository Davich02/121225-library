"""
Management command: seed_data

Generates fake data for the whole library app:
User, Group, Author, AuthorDetail, Category, Library,
Book, Post, Borrow, Review, Event, EventParticipant.

Usage:
    python manage.py seed_data
    python manage.py seed_data --users 20 --authors 8 --books 30
    python manage.py seed_data --flush
    python manage.py seed_data --password mypassword

Requires Faker:
    pip install Faker
"""

import random
from datetime import timedelta
from itertools import product

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from django.utils import timezone

from faker import Faker

from apps.core.models import Gender
from apps.library.models import (
    Author,
    AuthorDetail,
    Book,
    Borrow,
    Category,
    Event,
    EventParticipant,
    Library,
    Post,
    Review,
)

fake = Faker()
User = get_user_model()

DEFAULT_PASSWORD = "Passw0rd!"  # dev/seed only — never use in prod
GROUP_NAMES = ["Admin", "Employee", "Visitor"]


class Command(BaseCommand):
    help = "Generates fake data for every model in the library app using Faker."

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=20)
        parser.add_argument("--authors", type=int, default=8)
        parser.add_argument("--categories", type=int, default=5)
        parser.add_argument("--libraries", type=int, default=3)
        parser.add_argument("--books", type=int, default=30)
        parser.add_argument("--posts", type=int, default=15)
        parser.add_argument("--borrows", type=int, default=25)
        parser.add_argument("--reviews", type=int, default=40)
        parser.add_argument("--events", type=int, default=6)
        parser.add_argument("--event-participants", type=int, default=30)
        parser.add_argument(
            "--password",
            type=str,
            default=DEFAULT_PASSWORD,
            help="Password set for every generated User (dev only).",
        )
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete all existing seeded data before generating new data.",
        )

    def handle(self, *args, **options):
        if options["flush"]:
            self._flush()

        with transaction.atomic():
            groups = self._create_groups()
            users = self._create_users(options["users"], options["password"], groups)
            authors = self._create_authors(options["authors"])
            self._create_author_details(authors)
            categories = self._create_categories(options["categories"])
            libraries = self._create_libraries(options["libraries"])
            books = self._create_books(options["books"], authors, categories, libraries, users)
            posts = self._create_posts(options["posts"], users, libraries)
            borrows = self._create_borrows(options["borrows"], users, books, libraries)
            reviews = self._create_reviews(options["reviews"], books, users)
            events = self._create_events(options["events"], libraries, books)
            participants = self._create_event_participants(
                options["event_participants"], events, users
            )

        self.stdout.write(self.style.SUCCESS(
            "Done:\n"
            f"  users: {len(users)}\n"
            f"  authors: {len(authors)}\n"
            f"  categories: {len(categories)}\n"
            f"  libraries: {len(libraries)}\n"
            f"  books: {len(books)}\n"
            f"  posts: {len(posts)}\n"
            f"  borrows: {len(borrows)}\n"
            f"  reviews: {len(reviews)}\n"
            f"  events: {len(events)}\n"
            f"  event participants: {len(participants)}"
        ))

    # ------------------------------------------------------------------ #
    # Flush
    # ------------------------------------------------------------------ #

    def _flush(self):
        self.stdout.write(self.style.WARNING("Deleting existing data..."))
        # от зависимых моделей к базовым
        EventParticipant.objects.all().delete()
        Event.objects.all().delete()
        Review.objects.all().delete()
        Borrow.objects.all().delete()
        Post.objects.all().delete()
        Book.objects.all().delete()
        Library.objects.all().delete()
        Category.objects.all().delete()
        AuthorDetail.objects.all().delete()
        Author.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()  # superuser'ов не трогаем

    # ------------------------------------------------------------------ #
    # Users & Groups
    # ------------------------------------------------------------------ #

    def _create_groups(self):
        groups = []
        for name in GROUP_NAMES:
            group, _ = Group.objects.get_or_create(name=name)
            groups.append(group)
        return groups

    def _create_users(self, count, password, groups):
        users = []
        for _ in range(count):
            username = fake.unique.user_name()
            user = User.objects.create_user(
                username=username,
                email=fake.unique.email(),
                password=password,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                gender=random.choice(Gender.values),
                birth_date=fake.date_of_birth(minimum_age=14, maximum_age=90),
            )
            # каждому — 1-2 группы
            user.groups.set(random.sample(groups, k=random.randint(1, 2)))
            users.append(user)
        return users

    # ------------------------------------------------------------------ #
    # Author / AuthorDetail
    # ------------------------------------------------------------------ #

    def _create_authors(self, count):
        authors = []
        for _ in range(count):
            author = Author.objects.create(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                date_of_birth=fake.date_of_birth(minimum_age=25, maximum_age=90),
                profile=fake.url(),
                rating=fake.random_int(min=1, max=10),
            )
            authors.append(author)
        return authors

    def _create_author_details(self, authors, coverage=0.7):
        """Only a subset of authors get extended details, mimicking real data."""
        for author in authors:
            if random.random() > coverage:
                continue
            AuthorDetail.objects.create(
                author=author,
                biography=fake.paragraph(nb_sentences=8),
                birth_city=fake.city(),
                gender=random.choice(Gender.values),
            )

    # ------------------------------------------------------------------ #
    # Category / Library
    # ------------------------------------------------------------------ #

    def _create_categories(self, count):
        categories = []
        attempts, max_attempts = 0, count * 5
        while len(categories) < count and attempts < max_attempts:
            attempts += 1
            name = fake.unique.word().capitalize()
            category, created = Category.objects.get_or_create(name=name)
            if created:
                categories.append(category)
        return categories

    def _create_libraries(self, count):
        libraries = []
        attempts, max_attempts = 0, count * 5
        while len(libraries) < count and attempts < max_attempts:
            attempts += 1
            try:
                with transaction.atomic():
                    library = Library.objects.create(
                        name=f"{fake.company()} Library",
                        location=fake.unique.city(),
                        site=fake.url(),
                    )
                libraries.append(library)
            except IntegrityError:
                continue
        return libraries

    # ------------------------------------------------------------------ #
    # Book
    # ------------------------------------------------------------------ #

    def _create_books(self, count, authors, categories, libraries, users):
        books = []
        skipped = 0
        max_attempts_per_book = 20

        for _ in range(count):
            book = None
            for _attempt in range(max_attempts_per_book):
                try:
                    with transaction.atomic():
                        book = Book.objects.create(
                            title=fake.sentence(nb_words=4).rstrip("."),
                            author=random.choice(authors) if authors else None,
                            published_at=fake.date_between(start_date="-40y", end_date="today"),
                            genre=random.choice(Book.Genre.values),
                            page_count=fake.random_int(min=50, max=900),
                            category=random.choice(categories) if categories else None,
                            publisher=random.choice(users) if users else None,
                            description=fake.paragraph(nb_sentences=5),
                        )
                        if libraries:
                            book.libraries.set(
                                random.sample(libraries, k=random.randint(1, min(3, len(libraries))))
                            )
                    break
                except IntegrityError:
                    continue

            if book is None:
                skipped += 1
                continue
            books.append(book)

        if skipped:
            self.stdout.write(self.style.WARNING(
                f"Skipped {skipped} book(s): unique_together collisions on "
                f"author/title or author/published_at. Consider increasing --authors."
            ))
        return books

    # ------------------------------------------------------------------ #
    # Post
    # ------------------------------------------------------------------ #

    def _create_posts(self, count, users, libraries):
        if not libraries:
            self.stdout.write(self.style.WARNING("No libraries — skipping posts."))
            return []

        posts = []
        for _ in range(count):
            post = Post.objects.create(
                title=fake.sentence(nb_words=6).rstrip("."),
                body=fake.paragraph(nb_sentences=6),
                author=random.choice(users) if users else None,
                moderated=fake.boolean(chance_of_getting_true=70),
                library=random.choice(libraries),
            )
            posts.append(post)
        return posts

    # ------------------------------------------------------------------ #
    # Borrow
    # ------------------------------------------------------------------ #

    def _create_borrows(self, count, users, books, libraries):
        if not (users and books):
            self.stdout.write(self.style.WARNING("No users/books — skipping borrows."))
            return []

        today = timezone.now().date()
        borrows = []
        for _ in range(count):
            borrow_date = fake.date_between(start_date="-1y", end_date="today")
            return_date = borrow_date + timedelta(days=random.randint(7, 45))
            # книга считается возвращённой, если срок уже прошёл — с вероятностью 70%
            returned = return_date < today and fake.boolean(chance_of_getting_true=70)

            borrow = Borrow.objects.create(
                member=random.choice(users),
                book=random.choice(books),
                library=random.choice(libraries) if libraries else None,
                borrow_date=borrow_date,
                return_date=return_date,
                returned=returned,
            )
            borrows.append(borrow)
        return borrows

    # ------------------------------------------------------------------ #
    # Review (unique_together: book, reviewer)
    # ------------------------------------------------------------------ #

    def _create_reviews(self, count, books, users):
        if not (books and users):
            self.stdout.write(self.style.WARNING("No books/users — skipping reviews."))
            return []

        possible_pairs = list(product(books, users))
        random.shuffle(possible_pairs)
        count = min(count, len(possible_pairs))  # больше уникальных пар, чем есть, не создать

        reviews = []
        for book, reviewer in possible_pairs[:count]:
            review = Review.objects.create(
                book=book,
                reviewer=reviewer,
                rating=round(random.uniform(1, 5), 1),
                description=fake.paragraph(nb_sentences=3),
            )
            reviews.append(review)
        return reviews

    # ------------------------------------------------------------------ #
    # Event
    # ------------------------------------------------------------------ #

    def _create_events(self, count, libraries, books):
        if not libraries:
            self.stdout.write(self.style.WARNING("No libraries — skipping events."))
            return []

        events = []
        for _ in range(count):
            naive_dt = fake.date_time_between(start_date="-6M", end_date="+6M")
            event_date = (
                timezone.make_aware(naive_dt) if settings.USE_TZ else naive_dt
            )
            event = Event.objects.create(
                title=fake.sentence(nb_words=5).rstrip("."),
                description=fake.paragraph(nb_sentences=4),
                date=event_date,
                library=random.choice(libraries),
            )
            if books:
                event.books.set(random.sample(books, k=random.randint(1, min(3, len(books)))))
            events.append(event)
        return events

    # ------------------------------------------------------------------ #
    # EventParticipant (unique_together: event, member)
    # ------------------------------------------------------------------ #

    def _create_event_participants(self, count, events, users):
        if not (events and users):
            self.stdout.write(self.style.WARNING("No events/users — skipping event participants."))
            return []

        possible_pairs = list(product(events, users))
        random.shuffle(possible_pairs)
        count = min(count, len(possible_pairs))

        participants = []
        for event, member in possible_pairs[:count]:
            participant = EventParticipant.objects.create(
                event=event,
                member=member,
                registration_date=fake.date_between(start_date="-3M", end_date="today"),
            )
            participants.append(participant)
        return participants