from django.db import models

class Pais(models.Model):
    nombre_pais = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre_pais

    class Meta:
        db_table = 'Paises'
        verbose_name = "País"
        verbose_name_plural = "Países"
