from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import admin
from django import forms
from django.template.loader import get_template

from apps.authentication.services import validate_password_in_forms

from .models import User
from ..clubs.admin import ClubBranchUserInline, ClubUserCashbackInline


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
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'mobile_phone', 'email', 'is_email_confirmed', 'is_staff',)
    list_filter = ('is_staff',)
    list_display_links = ('id', 'mobile_phone', 'email', 'is_staff',)
    search_fields = ('email', 'uuid', 'mobile_phone')
    filter_horizontal = ('groups', 'user_permissions',)
    add_form = UserCreationForm
    ordering = ['-created_at']
    inlines = [
        ClubUserCashbackInline,
        ClubBranchUserInline
    ]
    readonly_fields = ('club_user_cashback_inline',)

    fieldsets = (
        (None, {
            "fields": (
                'club_user_cashback_inline',
                'uuid',
                'mobile_phone',
                'email',
                'password',
                'club',
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
                'club',
                'is_superuser',
                'is_staff',
                'groups',
                'user_permissions',
            ),
        }),
        
    )

    def club_user_cashback_inline(self, *args, **kwargs):
        context = getattr(self.response, 'context_data', None) or {} # somtimes context.copy() is better
        inline = context['inline_admin_formset'] = context['inline_admin_formsets'].pop(0)
        return get_template(inline.opts.template).render(context, self.request)
    club_user_cashback_inline.short_description = "Кешбэк пользователя"

    def render_change_form(self, request, *args, **kwargs):
        self.request = request
        self.response = super().render_change_form(request, *args, **kwargs)
        return self.response
