# admin.py
from decimal import Decimal
from django.contrib import admin
from django import forms
from .models import Development, Stage, Lot

@admin.register(Development)
class DevelopmentAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")

@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ("development", "number", "is_active", "price_per_m2")
    list_filter = ("development", "is_active")
    search_fields = ("development__name",)

class LotAdminForm(forms.ModelForm):
    """Calcula área y precio en el clean para que el admin los vea ya rellenos."""
    class Meta:
        model = Lot
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        # Clonamos a la instancia temporalmente con los datos del form
        lot = self.instance
        for f, v in cleaned.items():
            setattr(lot, f, v)

        lot.recalc_fields()
        if lot.area_m2:
            cleaned["area_m2"] = lot.area_m2
        if lot.list_price:
            cleaned["list_price"] = lot.list_price
        return cleaned

@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    form = LotAdminForm
    list_display = ("code", "stage", "status", "area_m2", "list_price")
    list_filter  = ("stage__development", "stage", "status")
    search_fields = ("code", "block", "svg_id")

    fieldsets = (
        (None, {
            "fields": ("stage", "code", "block", "status", "svg_id", "tooltip_label", "plan_image")
        }),
        ("Dimensiones", {
            "fields": (
                ("front_m", "back_m", "left_m", "right_m"),
                ("frontage_m", "depth_m"),
            ),
            "description": "Para irregulares usa los 4 lados; para rectangulares, frente × fondo."
        }),
        ("Área y precio", {
            "fields": ("area_m2", "price_per_m2_override", "list_price"),
            "description": "Si dejas vacío el 'Precio por m² (override)', se usa el precio por m² de la etapa."
        }),
    )