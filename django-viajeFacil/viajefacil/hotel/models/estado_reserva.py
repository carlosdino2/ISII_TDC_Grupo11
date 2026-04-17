from django.db import models

class Estados_Reservas(models.Model):
    descripcion_estado_reserva = models.CharField(max_length=100)

    def __str__(self):
        return self.descripcion_estado_reserva

    class Meta:
        db_table = 'Estados_Reservas'
        verbose_name = 'Estado de Reserva'
        verbose_name_plural = 'Estados de Reservas'
