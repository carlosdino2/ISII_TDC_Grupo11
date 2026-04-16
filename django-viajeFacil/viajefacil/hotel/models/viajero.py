from django.db import models

class Viajeros(models.Model):
    identificacion_viajero = models.CharField(max_length=20)
    nombre_viajero = models.CharField(max_length=100)
    apellido_viajero = models.CharField(max_length=100)
    telefono_viajero = models.CharField(max_length=20)
    email_viajero = models.EmailField()
    fecha_nacimiento_viajero = models.DateField()
    clave_viajero = models.CharField(max_length=128)
    direccion = models.ForeignKey("hotel.Direccion", on_delete=models.CASCADE)

    class Meta:
        db_table = 'Viajeros'
        verbose_name = "Viajero"
        verbose_name_plural = "Viajeros"

    def __str__(self):
        return f"{self.nombre_viajero} {self.apellido_viajero}"