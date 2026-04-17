from django.db import models
from .servicios_hoteles import Servicios_Hoteles
from .servicio_categoria_habitacion import Servicios_Categorias_Habitaciones

class Categorias_Servicios(models.Model):
    servicio_hotel = models.ForeignKey(Servicios_Hoteles, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Servicios_Categorias_Habitaciones, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.servicio_hotel} - {self.categoria}"

    class Meta:
        db_table = 'Categorias_Servicios'
        unique_together = ('servicio_hotel', 'categoria')
        verbose_name = "Categoría Servicio"
        verbose_name_plural = "Categorías Servicios"
