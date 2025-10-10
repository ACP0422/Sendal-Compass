from django.db import models

class Project(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    default_lot_image = models.ImageField(upload_to="projects/default_lots/", blank=True, null=True)

    def __str__(self):
        return self.name


class Stage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="stages")
    name = models.CharField(max_length=80)

    # Parámetros centralizados y administrables
    down_payment_percent = models.DecimalField(max_digits=5, decimal_places=2, default=20.00)  # 20%
    apartar_amount       = models.DecimalField(max_digits=12, decimal_places=2, default=1000.00)
    deadline_days        = models.PositiveIntegerField(default=5)  # días posteriores al apartado

    class Meta:
        unique_together = ("project", "name")

    def __str__(self):
        return f"{self.project.name} – {self.name}"


class Lot(models.Model):
    class Status(models.TextChoices):
        DISPONIBLE = "disponible", "Disponible"
        APARTADO   = "apartado",   "Apartado"
        VENDIDO    = "vendido",    "Vendido"

    project   = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="lots")
    stage     = models.ForeignKey(Stage, on_delete=models.PROTECT, related_name="lots", null=True, blank=True)

    number    = models.PositiveIntegerField()
    status    = models.CharField(max_length=12, choices=Status.choices, default=Status.DISPONIBLE)

    # Medidas y área
    area_m2   = models.DecimalField(max_digits=10, decimal_places=2)
    # Regular (si aplica)
    regular_width_m   = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    regular_length_m  = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    # Irregular (lista de lados "10,30,9.8,29.7")
    irregular_sides_m = models.CharField(max_length=120, blank=True, default="")

    # Precio lista y multimedia
    precio_lista = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    image        = models.ImageField(upload_to="lots/%Y/%m/", blank=True, null=True)

    # UI (por si quieres guardar defaults)
    plazo_default_meses     = models.PositiveIntegerField(default=180)

    class Meta:
        unique_together = ("project", "number")

    def __str__(self):
        return f"{self.project.name} – Lote {self.number}"

    @property
    def display_image_url(self):
        if self.image:
            return self.image.url
        if self.project.default_lot_image:
            return self.project.default_lot_image.url
        return None

    # ---- CÁLCULOS DERIVADOS (fijos pero administrables por Stage)
    @property
    def down_payment_total(self):
        """Total de enganche = %etapa * precio_lista"""
        pct = (self.stage.down_payment_percent if self.stage else 20)
        return (self.precio_lista or 0) * (float(pct) / 100.0)

    @property
    def apartar_amount(self):
        return float(self.stage.apartar_amount if self.stage else 1000)

    @property
    def saldo_enganche(self):
        """Saldo de enganche = enganche_total - apartado"""
        return self.down_payment_total - self.apartar_amount

    @property
    def deadline_days(self):
        return int(self.stage.deadline_days if self.stage else 5)


class PaymentUpdate(models.Model):
    lot        = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name="payment_updates")
    label      = models.CharField(max_length=60, default="Actualización")
    amount     = models.DecimalField(max_digits=12, decimal_places=2)
    payments   = models.PositiveIntegerField(default=0)
    sort_order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.lot} – {self.label}"
