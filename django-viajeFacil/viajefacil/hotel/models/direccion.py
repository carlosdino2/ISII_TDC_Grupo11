from django.db import models
from .localidad import Localidad

class Direccion(models.Model):
    calle_direccion = models.CharField(max_length=255)
    numero_direccion = models.CharField(max_length=10)
    cod_postal = models.CharField(max_length=10)
    localidad = models.ForeignKey(Localidad, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.calle_direccion} {self.numero_direccion}, {self.localidad}"

    class Meta:
        db_table = 'Direcciones'
        verbose_name = "Direccion"
        verbose_name_plural = "Direcciones"