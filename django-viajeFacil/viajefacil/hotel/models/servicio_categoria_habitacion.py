from django.db import models
from .servicios_hoteles import Servicios_Hoteles
from .categoria import Categorias

class Servicios_Categorias_Habitaciones(models.Model):
    nombre_servicio = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.pk} - {self.nombre_servicio}"

    class Meta:
        db_table = 'Servicios_Categorias_Habitaciones'
        verbose_name = 'Servicio por Categoría de Habitación'
        verbose_name_plural = 'Servicios por Categorías de Habitaciones'
