from django.db import models
from .direccion import Direccion
from django.db import connection


class Hotel(models.Model):
    nombre_hotel = models.CharField(max_length=100)
    descripcion_hotel = models.TextField(null=True, blank=True)
    cantidad_estrellas_hotel = models.IntegerField()
    imagen_hotel = models.ImageField(upload_to='\hotel\static\img', null=True, blank=True)
    ID_direccion = models.ForeignKey(Direccion, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre_hotel

    class Meta:
        db_table = 'Hoteles'
        verbose_name = 'Hotel'
        verbose_name_plural = 'Hoteles'

