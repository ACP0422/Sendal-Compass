from django.db import models

class Project(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    default_lot_image = models.ImageField(
        upload_to="projects/default_lots/", blank=True, null=True
    )

    def __str__(self):
        return self.name


class Lot(models.Model):
    class Status(models.TextChoices):
        DISPONIBLE = "disponible", "Disponible"
        APARTADO   = "apartado",   "Apartado"
        VENDIDO    = "vendido",    "Vendido"

    project   = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="lots")
    number    = models.PositiveIntegerField()
    area_m2   = models.DecimalField(max_digits=10, decimal_places=2)
    status    = models.CharField(max_length=12, choices=Status.choices, default=Status.DISPONIBLE)

    # Imagen propia del lote (plano/render)
    image     = models.ImageField(upload_to="lots/%Y/%m/", blank=True, null=True)

    # Datos mostrados arriba del esquema (editables)
    apartado                      = models.DecimalField(max_digits=12, decimal_places=2, default=1000)
    saldo_enganche                = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    dias_limite_pago_enganche     = models.PositiveIntegerField(default=5)
    precio_lista                  = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Opcional: valores por defecto de selects
    plazo_default_meses           = models.PositiveIntegerField(default=180)
    metodo_enganche_default       = models.CharField(max_length=20, default="Monto")  # Monto | Porcentaje

    class Meta:
        unique_together = ("project", "number")

    def __str__(self):
        return f"{self.project.name} – Lote {self.number}"

    @property
    def display_image_url(self) -> str | None:
        """
        Regresa la imagen del lote; si no hay, usa la del proyecto; si tampoco,
        devuelve None para que el template muestre un placeholder.
        """
        if self.image:
            return self.image.url
        if self.project.default_lot_image:
            return self.project.default_lot_image.url
        return None


class PaymentUpdate(models.Model):
    """Filas del 'Esquema de pagos' (editables por lote)."""
    lot        = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name="payment_updates")
    label      = models.CharField(max_length=60, default="Actualización")
    amount     = models.DecimalField(max_digits=12, decimal_places=2)
    payments   = models.PositiveIntegerField(default=0)  # ej. 60
    sort_order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.lot} – {self.label}"
