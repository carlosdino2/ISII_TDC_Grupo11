from django.db import models
from .hotel import Hotel
from .servicios_hoteles import Servicios_Hoteles

class Hoteles_Servicios(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    servicio_hotel = models.ForeignKey(Servicios_Hoteles, on_delete=models.CASCADE)

    class Meta:
        db_table = 'Hoteles_Servicios'
        unique_together = ('hotel', 'servicio_hotel')
        verbose_name = "Hoteles_Servicios"
        verbose_name_plural = "Hoteles_Servicios"

    def __str__(self):
        return f"{self.hotel} - {self.servicio_hotel}"
