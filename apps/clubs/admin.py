from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(ClubComputer)
admin.site.register(ClubUserInfo)


class ClubBranchInline(admin.StackedInline):
    model = ClubBranch
    extra = 0
    fields = ('name',)


class ClubBranchPropertyInline(admin.TabularInline):
    model = ClubBranchProperty
    extra = 0
    fields = ('hall_type', 'name')


class ClubBranchHardwareInline(admin.TabularInline):
    model = ClubBranchHardware
    extra = 0
    fields = ('hall_type', 'name')


class ClubBranchPriceInline(admin.TabularInline):
    model = ClubBranchPrice
    extra = 0
    fields = ('hall_type', 'name', 'price')


class ClubBranchComputerInline(admin.TabularInline):
    model = ClubComputer
    extra = 0
    fields = ('hall_type', 'number', 'is_booked')


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    fields = ('name', 'description')
    inlines = [ClubBranchInline]


@admin.register(ClubBranch)
class ClubBranchAdmin(admin.ModelAdmin):
    fields = ('name', 'address', 'club')
    inlines = [
        ClubBranchPropertyInline,
        ClubBranchHardwareInline,
        ClubBranchPriceInline,
        ClubBranchComputerInline
    ]
