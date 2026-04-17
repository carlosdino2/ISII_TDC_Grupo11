from django.db import models
from .pais import Pais

class Provincia(models.Model):
    nombre_provincia = models.CharField(max_length=100)
    pais = models.ForeignKey(Pais, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nombre_provincia}, {self.pais.nombre_pais}"

    class Meta:
        db_table = 'Provincias'
        verbose_name = "Provincia"
        verbose_name_plural = "Provincias" 