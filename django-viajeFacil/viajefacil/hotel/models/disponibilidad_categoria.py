from django.db import models
from .categoria import Categorias

class Disponibilidad_Categorias(models.Model):
    fecha = models.DateField()
    cantidad_disponible = models.PositiveIntegerField()
    categoria = models.ForeignKey(Categorias, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.categoria} ({self.fecha}): {self.cantidad_disponible}"

    class Meta:
        db_table = 'Disponibilidad_Categorias'
        unique_together = ('categoria', 'fecha')
        verbose_name = "Disponibilidad_Categorias"
        verbose_name_plural = "Disponibilidad_Categorias"