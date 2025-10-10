from django.contrib import admin
from .models import Project, Stage, Lot, PaymentUpdate

class PaymentUpdateInline(admin.TabularInline):
    model = PaymentUpdate
    extra = 1
    fields = ("sort_order", "label", "amount", "payments")
    ordering = ("sort_order",)

@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    list_display  = ("project", "stage", "number", "status", "area_m2", "precio_lista")
    list_filter   = ("project", "stage", "status")
    search_fields = ("number", "project__name", "stage__name")
    inlines       = [PaymentUpdateInline]

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display  = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ("project", "name", "down_payment_percent", "apartar_amount", "deadline_days")
    list_filter  = ("project",)
