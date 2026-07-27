from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    list_display = (
        "username", "email", "first_name", "last_name",
        "gender", "age_display", "is_staff", "is_active", "date_joined",
    )
    list_filter = ("is_staff", "is_active", "is_superuser", "gender", "groups")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("-date_joined",)
    filter_horizontal = ("groups", "user_permissions", "libraries")
    readonly_fields = ("date_joined", "last_login", "age_display")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {
            "fields": (
                "first_name", "last_name", "email",
                "gender", "birth_date", "age_display", "avatar",
            )
        }),
        (_("Library"), {"fields": ("libraries",)}),
        (_("Permissions"), {
            "fields": (
                "is_active", "is_staff", "is_superuser",
                "groups", "user_permissions",
            )
        }),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2"),
        }),
    )

    @admin.display(description=_("Age"))
    def age_display(self, obj):
        return obj.age if obj.age is not None else "—"