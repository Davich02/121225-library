from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.conf import settings

from apps.core.models import UUIDModel, TimeStampedModel, Gender, age_validator


class Author(UUIDModel, TimeStampedModel):
    first_name = models.CharField(max_length=50, verbose_name=_('First Name'))
    last_name = models.CharField(max_length=50, verbose_name=_('Last Name'))
    date_of_birth = models.DateField(
        validators=[age_validator],
        verbose_name=_('Date of Birth'),
    )
    profile = models.URLField(blank=True, verbose_name=_('Profile URL'))
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name=_('Rating')
    )

    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Deleted at'))

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def __str__(self):
        return f'{self.first_name[0]}. {self.last_name}; {self.date_of_birth}'

    class Meta:
        db_table = 'authors'


class AuthorDetail(TimeStampedModel):
    author = models.OneToOneField(
        Author,
        on_delete=models.CASCADE,
        related_name='details',
        verbose_name=_('Author')
    )

    biography = models.TextField(blank=True, verbose_name=_('Biography'))
    birth_city = models.CharField(blank=True, max_length=50, verbose_name=_('Birth City'))
    gender = models.CharField(choices=Gender.choices, max_length=1, verbose_name=_('Gender'))

    class Meta:
        verbose_name = _('Author Detail')
        verbose_name_plural = _('Author Details')

    def __str__(self):
        return f'Details of {self.author}'


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name=_('Name'))

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def __str__(self):
        return self.name


class Library(UUIDModel, TimeStampedModel):
    name = models.CharField(max_length=50, verbose_name=_('Name'))
    location = models.CharField(max_length=50, unique=True, verbose_name=_('Location'))
    site = models.URLField(blank=True, verbose_name=_('Site'))
    slug = models.SlugField(max_length=70, unique=True, blank=True, verbose_name=_('Slug'))

    class Meta:
        verbose_name = _('Library')
        verbose_name_plural = _('Libraries')
        ordering = ['-created_at']
        get_latest_by = 'created_at'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            # защита от коллизий: Library с одинаковым name даст одинаковый slug
            while Library.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Book(UUIDModel, TimeStampedModel):
    class Genre(models.TextChoices):
        FICTION = 'Fiction', _('Fiction')
        NON_FICTION = 'Non-Fiction', _('Non-Fiction')
        HORROR = 'Horror', _('Horror')
        HISTORY = 'History', _('History')

    title = models.CharField(max_length=50, verbose_name=_('Title'), db_index=True)
    author = models.ForeignKey(
        Author,
        null=True,
        blank=True,
        related_name='books',
        on_delete=models.SET_NULL,
        verbose_name=_('Author')
    )

    published_at = models.DateField(verbose_name=_('Published at'))
    genre = models.CharField(choices=Genre.choices, max_length=20, verbose_name=_('Genre'))
    page_count = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10000)],
        verbose_name=_('Page Count')
    )
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        related_name='books',
        on_delete=models.SET_NULL,
        verbose_name=_('Category')
    )
    publisher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name='published_books',
        on_delete=models.SET_NULL,
        verbose_name=_('Publisher')
    )
    libraries = models.ManyToManyField(Library, verbose_name=_('Libraries'), blank=True, related_name='books')
    description = models.TextField(blank=True, verbose_name=_('Summary'))
    photo = models.ImageField(upload_to='books', blank=True, verbose_name=_('Photo'))

    class Meta:
        db_table = 'library_books'
        verbose_name = _('Book')
        verbose_name_plural = _('Books')
        ordering = ('-published_at',)
        unique_together = (('author', 'title'), ('author', 'published_at'))
        get_latest_by = 'created_at'
        indexes = [
            models.Index(fields=['title', 'author']),
            models.Index(fields=['published_at'], name='published_at_idx'),
        ]

    @property
    def rating_python(self):
        items = self.reviews.all()
        return sum(item.rating for item in items) / len(items) if len(items) else 0

    @property
    def rating_db(self):
        from django.db.models import Avg, Count, Min, Max, Sum
        mean = self.reviews.aggregate(mean=Avg('rating'))['mean']
        return round(mean, 2) if mean is not None else 0

    def __str__(self):
        return self.title


class Post(TimeStampedModel):
    title = models.CharField(max_length=50, verbose_name=_('Title'))
    body = models.TextField(verbose_name=_('Body'))
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name=_('Author'),
    )

    moderated = models.BooleanField(default=False, verbose_name=_('Moderated'))
    library = models.ForeignKey(
        Library,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name=_('Library')
    )

    class Meta:
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')

    def __str__(self):
        return f'{self.title} - {self.author} - {self.body[:20]}'


class Borrow(TimeStampedModel):
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='borrows',
        verbose_name=_('Member')
    )
    book = models.ForeignKey(
        Book,
        null=True,
        blank=True,
        related_name='borrows',
        on_delete=models.SET_NULL,
        verbose_name=_('Book')
    )
    library = models.ForeignKey(
        Library,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='borrows',
        verbose_name=_('Library')
    )
    borrow_date = models.DateField(verbose_name=_('Borrow date'))
    return_date = models.DateField(verbose_name=_('Return date'))
    returned = models.BooleanField(default=False, verbose_name=_('Returned'))

    class Meta:
        verbose_name = _('Borrow')
        verbose_name_plural = _('Borrows')

    @property
    def is_overdue(self):
        if self.returned:
            return False
        return self.return_date < timezone.now().date()

    def __str__(self):
        return f'{self.member} - {self.book} - {self.return_date}'


class Review(TimeStampedModel):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviews'
    )
    rating = models.FloatField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    description = models.TextField()

    class Meta:
        verbose_name = _('Review')
        verbose_name_plural = _('Reviews')
        unique_together = ('book', 'reviewer')  # один отзыв на книгу от пользователя

    def __str__(self):
        return f'Review of {self.book} by {self.reviewer}'


class Event(UUIDModel, TimeStampedModel):
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    description = models.TextField(verbose_name=_('Description'))
    date = models.DateTimeField(verbose_name=_('Date'))
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='events')
    books = models.ManyToManyField(Book, related_name='events', blank=True)

    class Meta:
        verbose_name = _('Event')
        verbose_name_plural = _('Events')

    def __str__(self):
        return self.title


class EventParticipant(TimeStampedModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='participants')
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='event_participations'
    )
    registration_date = models.DateField(default=timezone.localdate, verbose_name=_('Registration date'))

    class Meta:
        verbose_name = _('Event Participant')
        verbose_name_plural = _('Event Participants')
        unique_together = ('event', 'member')  # нельзя зарегистрироваться дважды

    def __str__(self):
        return f'{self.member} on {self.event}'