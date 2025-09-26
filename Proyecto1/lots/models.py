from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify

Q2 = Decimal("0.01")
def q2(x: Decimal | float | int | None) -> Decimal | None:
    """Redondea a 2 decimales usando HALF_UP."""
    if x is None:
        return None
    return Decimal(x).quantize(Q2, rounding=ROUND_HALF_UP)


class Development(models.Model):
    name = models.CharField(
        max_length=120,
        verbose_name=_("Nombre del desarrollo"),
        help_text=_("Ej.: 'Hacienda Residencial'.")
    )
    slug = models.SlugField(
        unique=True,
        verbose_name=_("Identificador (slug)"),
        help_text=_("Se usa en la URL. Ej.: 'hacienda-residencial'.")
    )

    class Meta:
        verbose_name = _("Desarrollo")
        verbose_name_plural = _("Desarrollos")

    def __str__(self):
        return self.name


class Stage(models.Model):
    development = models.ForeignKey(
        Development, on_delete=models.CASCADE, related_name="stages",
        verbose_name=_("Desarrollo")
    )
    number = models.PositiveIntegerField(
        verbose_name=_("Número de etapa"),
        help_text=_("1, 2, 3…")
    )
    is_active = models.BooleanField(
        default=False, verbose_name=_("Activa"),
        help_text=_("Marque si esta etapa es la vigente.")
    )
    price_per_m2 = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name=_("Precio por m² (etapa)"),
        help_text=_("Se aplica a los lotes si no tienen un precio por m² específico.")
    )

    class Meta:
        unique_together = ("development", "number")
        verbose_name = _("Etapa")
        verbose_name_plural = _("Etapas")

    def __str__(self):
        return f"{self.development.name} – Etapa {self.number}"


class Lot(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", _("Disponible")
        RESERVED  = "reserved",  _("Apartado")
        SOLD      = "sold",      _("Vendido")

    # Identificación
    stage = models.ForeignKey(
        Stage, on_delete=models.CASCADE, related_name="lots", verbose_name=_("Etapa")
    )
    code = models.CharField(
        _("Código de lote"), max_length=20,
        help_text=_("Ej.: 'A-12' o '45'.")
    )
    status = models.CharField(
        _("Estatus"), max_length=12, choices=Status.choices, default=Status.AVAILABLE
    )

    # —— Dimensiones (puede capturarse como irregular o regular)
    # Irregular (4 lados)
    front_m  = models.DecimalField(_("Frente superior (m)"), max_digits=7, decimal_places=2, null=True, blank=True)
    back_m   = models.DecimalField(_("Fondo inferior (m)"),  max_digits=7, decimal_places=2, null=True, blank=True)
    left_m   = models.DecimalField(_("Lado izquierdo (m)"),  max_digits=7, decimal_places=2, null=True, blank=True)
    right_m  = models.DecimalField(_("Lado derecho (m)"),    max_digits=7, decimal_places=2, null=True, blank=True)
    # Regular (frente × fondo)
    frontage_m = models.DecimalField(_("Frente (m)"), max_digits=7, decimal_places=2, null=True, blank=True)
    depth_m    = models.DecimalField(_("Fondo (m)"),  max_digits=7, decimal_places=2, null=True, blank=True)

    # —— Área y precios
    area_m2 = models.DecimalField(
        _("Área (m²)"), max_digits=9, decimal_places=2, null=True, blank=True,
        help_text=_("Si se deja vacío, se calcula automáticamente con las medidas.")
    )
    price_per_m2_override = models.DecimalField(
        _("Precio por m² (específico)"), max_digits=10, decimal_places=2, null=True, blank=True,
        help_text=_("Opcional. Si no se llena, se usa el precio por m² de la etapa.")
    )
    list_price = models.DecimalField(
        _("Precio de lista"), max_digits=12, decimal_places=2, null=True, blank=True,
        help_text=_("Se calcula automáticamente: Área × Precio por m².")
    )

    # —— Mapa (ocultos en admin; se autogeneran)
    svg_id = models.CharField(
        _("ID del polígono (SVG)"), max_length=40, unique=True, blank=True
    )
    tooltip_label = models.CharField(
        _("Texto para tooltip"), max_length=120, blank=True
    )

    class Meta:
        ordering = ["code"]
        verbose_name = _("Lote")
        verbose_name_plural = _("Lotes")

    def __str__(self):
        return f"{self.code} (Etapa {self.stage.number})"

    def get_absolute_url(self):
        return reverse("lot_detail", kwargs={
            "development_slug": self.stage.development.slug,
            "stage_number": self.stage.number,
            "lot_code": self.code,
        })

    # ===== Cálculos
    def compute_area_from_sides(self) -> Decimal | None:
        """
        Calcula el área:
        - Si hay 4 lados: promedio de frentes × promedio de costados (aprox. trapecio/romboide).
        - Si no, y hay Frente×Fondo: multiplicación directa.
        """
        if all(v is not None for v in (self.front_m, self.back_m, self.left_m, self.right_m)):
            width = (Decimal(self.front_m) + Decimal(self.back_m)) / Decimal(2)
            depth = (Decimal(self.left_m) + Decimal(self.right_m)) / Decimal(2)
            return q2(width * depth)
        if self.frontage_m is not None and self.depth_m is not None:
            return q2(Decimal(self.frontage_m) * Decimal(self.depth_m))
        return None

    def effective_price_per_m2(self) -> Decimal:
        """Override > precio de la etapa > 0."""
        return Decimal(self.price_per_m2_override or self.stage.price_per_m2 or 0)

    # ===== Autogeneración de campos de mapa
    def _ensure_unique_svg_id(self, base: str) -> str:
        base = base[:36]  # deja espacio para sufijos
        candidate = base
        i = 1
        while Lot.objects.exclude(pk=self.pk).filter(svg_id=candidate).exists():
            suffix = f"-{i}"
            candidate = (base + suffix)[:40]
            i += 1
        return candidate

    def _auto_svg_id(self) -> str:
        # Patrón estable y legible, consistente con la etiqueta:
        # "Lote <code>" → id: "<slugdev>-e<etapa>-l-<code-slug>"
        dev = slugify(self.stage.development.slug or self.stage.development.name)
        code = slugify(self.code)  # “A-12” → “a-12”
        base = f"{dev}-e{self.stage.number}-l-{code}"
        return self._ensure_unique_svg_id(base)

    # ===== Validación y autollenado
    def clean(self):
        super().clean()

        # Permitir: 4 lados (irregular) O frente×fondo (regular) O área manual.
        sides = [self.front_m, self.back_m, self.left_m, self.right_m]
        pair  = [self.frontage_m, self.depth_m]
        has_any  = any(v is not None for v in sides + pair)
        has_sides = all(v is not None for v in sides)
        has_pair  = all(v is not None for v in pair)

        if has_any and not (has_sides or has_pair or self.area_m2 is not None):
            raise ValidationError(_("Capture las cuatro medidas (irregular), o Frente × Fondo (regular), o bien el Área manual."))

        # Área: si el admin la escribió, se respeta; si no, se calcula.
        if self.area_m2 is None:
            self.area_m2 = self.compute_area_from_sides()

        # Precio de lista: siempre que haya área.
        if self.area_m2 is not None:
            self.list_price = q2(Decimal(self.area_m2) * self.effective_price_per_m2())

        # Autollenado mapa (oculto en admin)
        if not self.svg_id and self.stage_id and self.code:
            self.svg_id = self._auto_svg_id()

        if not self.tooltip_label:
            # Igual que la etiqueta “visible”: “Lote <código> · <área> m²”
            base = f"Lote {self.code}"
            self.tooltip_label = base + (f" · {self.area_m2} m²" if self.area_m2 is not None else "")

    def save(self, *args, **kwargs):
        # Garantiza cálculos/auto-IDs incluso si no pasa por formularios
        self.full_clean()
        return super().save(*args, **kwargs)

    # Compatibilidad para acciones del admin
    def recalc_fields(self):
        if self.area_m2 is None:
            self.area_m2 = self.compute_area_from_sides()
        if self.area_m2 is not None:
            self.list_price = q2(Decimal(self.area_m2) * self.effective_price_per_m2())
        if not self.svg_id and self.stage_id and self.code:
            self.svg_id = self._auto_svg_id()
        if not self.tooltip_label:
            base = f"Lote {self.code}"
            self.tooltip_label = base + (f" · {self.area_m2} m²" if self.area_m2 is not None else "")
