from django.db import models

class Categorias(models.Model):
    nombre_categoria = models.CharField(max_length=50)
    descripcion_categoria = models.TextField(null=True, blank=True)
    capacidad_categoria = models.IntegerField()
    #imagen_categoria = models.ImageField(upload_to='/hotel/static/img', null=True, blank=True)
    precio_categoria = models.FloatField()

    def __str__(self):
        return self.nombre_categoria

    class Meta:
        db_table = 'Categorias'
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
