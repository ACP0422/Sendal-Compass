# apps/lots/admin.py
from django.contrib import admin
from .models import Project, Lot, PaymentUpdate

class PaymentUpdateInline(admin.TabularInline):
    model = PaymentUpdate
    extra = 1
    fields = ("sort_order", "label", "amount", "payments")
    ordering = ("sort_order",)

@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    list_display  = ("project", "number", "status", "area_m2", "precio_lista")
    list_filter   = ("project", "status")
    search_fields = ("number", "project__name")
    inlines       = [PaymentUpdateInline]

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display  = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
