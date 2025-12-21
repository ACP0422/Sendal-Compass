from django.db import models

class Lot(models.Model):
    id_lote = models.CharField(max_length=20, unique=True, db_index=True)

    estado_lote = models.CharField(max_length=50, blank=True, null=True)

    precio_total = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    precio_m2 = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    superficie_m2 = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    proyecto = models.CharField(max_length=120, blank=True, null=True)
    manzana = models.CharField(max_length=50, blank=True, null=True)

    medidas_lotes = models.CharField(max_length=120, blank=True, null=True)

    cantidad_de_apartado = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    dias_limite_apartado = models.IntegerField(blank=True, null=True)

    cantidad_enganche = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    cantidad_financiamiento = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    pago_mensualidad = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    cantidad_liquidacion = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)

    url_imagen_lote = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.id_lote
