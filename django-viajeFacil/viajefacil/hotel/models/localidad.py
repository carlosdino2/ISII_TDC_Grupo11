from django.db import models
from .provincia import Provincia

class Localidad(models.Model):
    id_localidad = models.AutoField(primary_key=True, db_column='ID_localidad')
    
    nombre_localidad = models.CharField(max_length=150, db_column='nombre_localidad')
    
    provincia = models.ForeignKey(
        Provincia, 
        on_delete=models.CASCADE, 
        db_column='ID_provincia'
    )

    def __str__(self):
        return f"{self.nombre_localidad}, {self.provincia.nombre_provincia}"

    class Meta:
        managed = False  # Recomendado si la tabla ya existe en SQL Server
        db_table = 'Localidades'
        verbose_name = 'Localidad'
        verbose_name_plural = 'Localidades'