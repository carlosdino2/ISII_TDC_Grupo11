from django.db import models
from .provincia import Provincia

class Localidad(models.Model):
    nombre_localidad = models.CharField(max_length=100)
    provincia = models.ForeignKey(Provincia, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nombre_localidad}, {self.provincia.nombre_provincia}"

    class Meta:
        db_table = 'Localidades'
        verbose_name = 'Localidad'
        verbose_name_plural = 'Localidades' 
