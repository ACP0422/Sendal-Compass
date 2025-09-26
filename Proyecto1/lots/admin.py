from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from .models import Development, Stage, Lot

# Encabezados del admin (en español)
admin.site.site_header = "Administración del Sitio"
admin.site.site_title  = "Panel de Administración"
admin.site.index_title = "Panel principal"

@admin.register(Development)
class DevelopmentAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        (_("Datos del desarrollo"), {
            "fields": ("name", "slug"),
            "description": _("El 'slug' se genera a partir del nombre (puede ajustarse).")
        }),
    )


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display  = ("development", "number", "is_active", "price_per_m2")
    list_filter   = ("development", "is_active")
    search_fields = ("development__name",)
    fieldsets = (
        (_("Etapa"), {
            "fields": ("development", "number", "is_active"),
            "description": _("Use un número consecutivo (1, 2, 3…).")
        }),
        (_("Precio base"), {
            "fields": ("price_per_m2",),
            "description": _("Precio por m² que se aplicará a los lotes si no tienen uno específico.")
        }),
    )


@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    # Listado
    list_display  = ("code", "stage", "status", "area_m2", "list_price")
    list_filter   = ("stage__development", "stage", "status")
    search_fields = ("code", "svg_id")

    # Precio es automático; el área es editable (se puede sobrescribir)
    readonly_fields = ("list_price",)

    # Ocultamos los campos de mapa al administrador (se generan solos)
    exclude = ("svg_id", "tooltip_label")

    fieldsets = (
        (_("Identificación"), {
            "fields": ("stage", "code", "status"),
            "description": _("Defina la etapa, el código visible del lote y su estatus.")
        }),
        (_("Medidas del lote"), {
            "fields": (
                ("front_m", "back_m", "left_m", "right_m"),
                ("frontage_m", "depth_m"),
            ),
            "description": _(
                "Capture las <b>4 medidas</b> para lotes <b>irregulares</b> "
                "o <b>Frente × Fondo</b> para lotes <b>regulares</b>. "
                "Si lo prefiere, deje las medidas vacías y capture el <b>Área</b> manualmente."
            )
        }),
        (_("Área y precio"), {
            "fields": ("area_m2", "price_per_m2_override", "list_price"),
            "description": _(
                "El <b>Área (m²)</b> se calcula sola a partir de las medidas, "
                "pero <b>puede sobrescribirse</b>. "
                "El <b>Precio de lista</b> se calcula automáticamente (Área × Precio por m²)."
            )
        }),
        # No mostramos “Mapa”: svg_id y tooltip se llenan solos.
    )

    @admin.action(description=_("Recalcular área y precio de los lotes seleccionados"))
    def recalc_selected(self, request, queryset):
        updated = 0
        for lot in queryset:
            lot.recalc_fields()
            lot.save(update_fields=["area_m2", "list_price", "svg_id", "tooltip_label"])
            updated += 1
        messages.success(request, _(f"Se recalcularon {updated} lote(s)."))

    actions = [recalc_selected]
