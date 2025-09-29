# models.py
from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.urls import reverse

Q2 = Decimal("0.01")
def q2(x: Decimal) -> Decimal:
    """Redondea a 2 decimales."""
    return x.quantize(Q2, rounding=ROUND_HALF_UP)


class Development(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    def __str__(self): return self.name


class Stage(models.Model):
    development = models.ForeignKey(Development, on_delete=models.CASCADE, related_name="stages")
    number = models.PositiveIntegerField()
    is_active = models.BooleanField(default=False)

    # Precio base por m² para esta etapa
    price_per_m2 = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ("development", "number")

    def __str__(self):
        return f"{self.development.name} – Etapa {self.number}"


class Lot(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Disponible"
        RESERVED  = "reserved",  "Apartado"
        SOLD      = "sold",      "Vendido"

    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name="lots")
    code = models.CharField(max_length=20)
    block = models.CharField(max_length=20, blank=True, null=True)  # <- agrega null=True

    # —— Dimensiones (opción 1: 4 lados para irregulares; opción 2: frente × fondo)
    front_m  = models.DecimalField("Frente (m)",  max_digits=7, decimal_places=2, null=True, blank=True)
    back_m   = models.DecimalField("Fondo (m)",   max_digits=7, decimal_places=2, null=True, blank=True)
    left_m   = models.DecimalField("Lado izq. (m)", max_digits=7, decimal_places=2, null=True, blank=True)
    right_m  = models.DecimalField("Lado der. (m)", max_digits=7, decimal_places=2, null=True, blank=True)
    frontage_m = models.DecimalField("Frontage m", max_digits=7, decimal_places=2, null=True, blank=True)
    depth_m    = models.DecimalField("Depth m",    max_digits=7, decimal_places=2, null=True, blank=True)

    # —— Derivados
    area_m2 = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    price_per_m2_override = models.DecimalField(
        "Price per m2 override", max_digits=10, decimal_places=2, null=True, blank=True
    )
    list_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    status = models.CharField(max_length=12, choices=Status.choices, default=Status.AVAILABLE)

    # Conectar con el SVG
    svg_id = models.CharField(max_length=40, unique=True)
    tooltip_label = models.CharField(max_length=120, blank=True)
    plan_image = models.ImageField(upload_to="lots/plans/", blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} (Etapa {self.stage.number})"

    def get_absolute_url(self):
        return reverse("lot_detail", kwargs={
            "development_slug": self.stage.development.slug,
            "stage_number": self.stage.number,
            "lot_code": self.code,
        })

    # ====== Cálculos ======
    def compute_area(self):
        """
        Si hay 4 lados -> promedio (trapecio/romboide aproximado).
        Si no, usa frente×fondo.
        """
        D = Decimal
        if all(v is not None for v in (self.front_m, self.back_m, self.left_m, self.right_m)):
            width = (D(self.front_m) + D(self.back_m)) / D(2)   # promedio de frentes
            depth = (D(self.left_m) + D(self.right_m)) / D(2)   # promedio de costados
            return q2(width * depth)
        if self.frontage_m is not None and self.depth_m is not None:
            return q2(D(self.frontage_m) * D(self.depth_m))
        return None

    def effective_price_per_m2(self) -> Decimal:
        """Override > precio de la etapa > 0."""
        return self.price_per_m2_override or self.stage.price_per_m2 or Decimal("0")

    def compute_price(self, area=None):
        area = area if area is not None else self.area_m2
        if not area:
            return None
        return q2(Decimal(area) * Decimal(self.effective_price_per_m2()))

    # Se recalcula SIEMPRE antes de guardar
    def clean(self):
        super().clean()
        area = self.compute_area()
        if area is not None:
            self.area_m2 = area
        price = self.compute_price(area)
        if price is not None:
            self.list_price = price

    def save(self, *args, **kwargs):
        # Garantiza que se apliquen los cálculos incluso si el admin no llama clean()
        self.full_clean()
        return super().save(*args, **kwargs)

    # —— Alias de compatibilidad para admins viejos que llamaban recalc_fields()
    def recalc_fields(self):
        """Compat: recalcula área y precio."""
        self.clean()