from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import admin
from django import forms

from apps.authentication.services import validate_password_in_forms

from .models import User


class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Повторите Пароль', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email',)

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        validate_password_in_forms(password1, password2)

        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'username', 'is_email_confirmed',)
    list_filter = ('is_staff',)
    list_display_links = ('id', 'username',)
    search_fields = ('email', 'uuid',)
    filter_horizontal = ('groups', 'user_permissions',)
    add_form = UserCreationForm
    ordering = ['-created_at']

    fieldsets = (
        (None, {
            "fields": (
                'uuid',
                'mobile_phone',
                'email',
                'password',
                'is_superuser',
                'is_active',
                'is_staff',
                'is_email_confirmed',
                'groups',
                'user_permissions',
                'created_at',
            )
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'password1',
                'password2',
                'is_superuser',
                'is_staff',
                'groups',
                'user_permissions',
            ),
        }),
    )
