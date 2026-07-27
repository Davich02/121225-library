from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    Author, AuthorDetail, Book, Borrow, Category,
    Event, EventParticipant, Library, Post, Review,
)


# ---------------------------------------------------------------- #
# Inlines
# ---------------------------------------------------------------- #

class AuthorDetailInline(admin.StackedInline):
    model = AuthorDetail
    extra = 0
    can_delete = False


class BookInline(admin.TabularInline):
    model = Book
    extra = 0
    fields = ("title", "genre", "published_at", "category")
    show_change_link = True


class EventParticipantInline(admin.TabularInline):
    model = EventParticipant
    extra = 0
    autocomplete_fields = ("member",)


# ---------------------------------------------------------------- #
# Author
# ---------------------------------------------------------------- #

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = (
        "first_name", "last_name", "date_of_birth",
        "rating", "is_deleted_display", "created_at",
    )
    list_filter = ("rating",)
    search_fields = ("first_name", "last_name")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "is_deleted_display")
    inlines = (AuthorDetailInline, BookInline)
    actions = ("soft_delete", "restore")

    @admin.display(description=_("Deleted"), boolean=True)
    def is_deleted_display(self, obj):
        return obj.is_deleted

    @admin.action(description=_("Soft-delete selected authors"))
    def soft_delete(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(deleted_at=timezone.now())
        self.message_user(request, f"{updated} author(s) soft-deleted.")

    @admin.action(description=_("Restore selected authors"))
    def restore(self, request, queryset):
        updated = queryset.update(deleted_at=None)
        self.message_user(request, f"{updated} author(s) restored.")


# ---------------------------------------------------------------- #
# Category
# ---------------------------------------------------------------- #

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


# ---------------------------------------------------------------- #
# Library
# ---------------------------------------------------------------- #

@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "slug", "created_at")
    search_fields = ("name", "location")
    readonly_fields = ("slug", "created_at", "updated_at")  # slug генерируется в save()
    ordering = ("-created_at",)


# ---------------------------------------------------------------- #
# Book
# ---------------------------------------------------------------- #

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        "title", "author", "genre", "category",
        "published_at", "rating_display", "publisher",
    )
    list_filter = ("genre", "category", "libraries")
    search_fields = ("title", "author__first_name", "author__last_name")
    autocomplete_fields = ("author", "category", "publisher")
    filter_horizontal = ("libraries",)
    readonly_fields = ("created_at", "updated_at", "rating_display")
    list_select_related = ("author", "category", "publisher")
    date_hierarchy = "published_at"

    @admin.display(description=_("Rating"))
    def rating_display(self, obj):
        return obj.rating


# ---------------------------------------------------------------- #
# Post
# ---------------------------------------------------------------- #

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "library", "moderated", "created_at")
    list_filter = ("moderated", "library")
    search_fields = ("title", "body", "author__username")
    autocomplete_fields = ("author", "library")
    actions = ("mark_moderated", "mark_unmoderated")

    @admin.action(description=_("Mark selected posts as moderated"))
    def mark_moderated(self, request, queryset):
        updated = queryset.update(moderated=True)
        self.message_user(request, f"{updated} post(s) moderated.")

    @admin.action(description=_("Mark selected posts as unmoderated"))
    def mark_unmoderated(self, request, queryset):
        updated = queryset.update(moderated=False)
        self.message_user(request, f"{updated} post(s) unmoderated.")


# ---------------------------------------------------------------- #
# Borrow
# ---------------------------------------------------------------- #

@admin.register(Borrow)
class BorrowAdmin(admin.ModelAdmin):
    list_display = (
        "member", "book", "library", "borrow_date",
        "return_date", "returned", "is_overdue_display",
    )
    list_filter = ("returned", "library")
    search_fields = ("member__username", "book__title")
    autocomplete_fields = ("member", "book", "library")
    date_hierarchy = "borrow_date"

    @admin.display(description=_("Overdue"), boolean=True)
    def is_overdue_display(self, obj):
        return obj.is_overdue


# ---------------------------------------------------------------- #
# Review
# ---------------------------------------------------------------- #

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("book", "reviewer", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("book__title", "reviewer__username")
    autocomplete_fields = ("book", "reviewer")


# ---------------------------------------------------------------- #
# Event
# ---------------------------------------------------------------- #

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "library", "date", "participants_count")
    list_filter = ("library",)
    search_fields = ("title", "description")
    filter_horizontal = ("books",)
    autocomplete_fields = ("library",)
    inlines = (EventParticipantInline,)
    date_hierarchy = "date"

    @admin.display(description=_("Participants"))
    def participants_count(self, obj):
        return obj.participants.count()


@admin.register(EventParticipant)
class EventParticipantAdmin(admin.ModelAdmin):
    list_display = ("event", "member", "registration_date")
    search_fields = ("event__title", "member__username")
    autocomplete_fields = ("event", "member")