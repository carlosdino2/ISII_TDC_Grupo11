from django.db import models
from .hotel import Hotel
from .categoria import Categorias

class Hoteles_Categorias(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categorias, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.hotel} - {self.categoria}"

    class Meta:
        db_table = 'Hoteles_Categorias'
        unique_together = ('hotel', 'categoria')
        verbose_name = "Hotel_Categoria"
        verbose_name_plural = "Hoteles_Categorias"