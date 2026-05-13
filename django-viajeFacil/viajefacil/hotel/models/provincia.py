from django.db import models
from .pais import Pais

class Provincia(models.Model):
    id_provincia = models.AutoField(primary_key=True, db_column='ID_provincia')
    nombre_provincia = models.CharField(max_length=100, db_column='nombre_provincia')
    
    pais = models.ForeignKey(
        Pais, 
        on_delete=models.CASCADE, 
        db_column='ID_pais' 
    )

    def __str__(self):
        return self.nombre_provincia

    class Meta:
        managed = False
        db_table = 'Provincias'