from django.db import models

class Pais(models.Model):
    id_pais = models.AutoField(primary_key=True, db_column='ID_pais')
    nombre_pais = models.CharField(max_length=150, db_column='nombre_pais')
    

    def __str__(self):
        return self.nombre_pais

    class Meta:
        managed = False  # Recomendado si la tabla ya existe en SQL Server
        db_table = 'Paises'
        verbose_name = "País"
        verbose_name_plural = "Países"
