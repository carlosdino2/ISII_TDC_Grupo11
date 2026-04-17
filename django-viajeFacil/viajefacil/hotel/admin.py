from django.contrib import admin
from .models import (
    Pais, Provincia, Localidad, Direccion,
    Viajeros,
    Hotel, Categorias, Hoteles_Categorias,
    Servicios_Hoteles, Hoteles_Servicios,
    Servicios_Categorias_Habitaciones,
    Disponibilidad_Categorias, Categorias_Servicios,
    Estados_Reservas, Reservas_Hoteles, Reservas_Hoteles_Detalles
)


# ========== UBICACIÓN ==========
@admin.register(Pais)
class PaisAdmin(admin.ModelAdmin):
    list_display = ['nombre_pais']
    search_fields = ['nombre']


@admin.register(Provincia)
class ProvinciaAdmin(admin.ModelAdmin):
    list_display = ['nombre_provincia', 'pais']
    list_filter = ['pais']
    search_fields = ['nombre']


@admin.register(Localidad)
class LocalidadAdmin(admin.ModelAdmin):
    list_display = ['nombre_localidad', 'provincia']
    list_filter = ['provincia']
    search_fields = ['nombre']
        

@admin.register(Direccion)
class DireccionAdmin(admin.ModelAdmin):
    list_display = ['calle_direccion', 'numero_direccion', 'cod_postal', 'localidad']
    search_fields = ['calle', 'numero', 'localidad__cod_postal']

    def get_cod_postal(self, obj):
        return obj.localidad.cod_postal
    get_cod_postal.short_description = 'Código Postal'



# ========== VIAJERO ==========
@admin.register(Viajeros)
class ViajerosAdmin(admin.ModelAdmin):
    list_display = ['identificacion_viajero', 'nombre_viajero', 'apellido_viajero', 'email_viajero', 'telefono_viajero','fecha_nacimiento_viajero','clave_viajero','direccion']
    search_fields = ['nombre', 'apellido', 'email']


# ========== HOTEL & CATEGORÍA ==========
@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ['ID_direccion', 'nombre_hotel', 'cantidad_estrellas_hotel','imagen_hotel']
    search_fields = ['nombre_hotel']
    list_filter = ['cantidad_estrellas_hotel']

    def id_hotel(self, obj):
        return obj.ID_hotel
    id_hotel.admin_order_field = 'ID_hotel'
    id_hotel.short_description = 'ID'

    def nombre_hotel(self, obj):
        return obj.nombre_hotel
    nombre_hotel.admin_order_field = 'nombre_hotel'
    nombre_hotel.short_description = 'Nombre'

    def cantidad_estrellas_hotel(self, obj):
        return obj.cantidad_estrellas_hotel
    cantidad_estrellas_hotel.admin_order_field = 'cantidad_estrellas_hotel'
    cantidad_estrellas_hotel.short_description = 'Estrellas'

    def direccion_str(self, obj):
        # Mostrar la representación __str__ de la dirección relacionada o un texto si es None
        return str(obj.ID_direccion) if obj.ID_direccion else '-'
    direccion_str.short_description = 'Dirección'



@admin.register(Categorias)
class CategoriasAdmin(admin.ModelAdmin):
    list_display = ['nombre_categoria', 'capacidad_categoria','descripcion_categoria']
    search_fields = ['nombre_categoria']
    list_filter = ['capacidad_categoria']



@admin.register(Hoteles_Categorias)
class HotelesCategoriasAdmin(admin.ModelAdmin):
    list_display = ['hotel', 'categoria']
    #list_filter = ['ID_hotel', 'ID_categoria']
    #search_fields = ['ID_hotel__nombre', 'ID_categoria__nombre']

    def hotel_nombre(self, obj):
        return obj.ID_hotel.nombre
    hotel_nombre.admin_order_field = 'ID_hotel'
    hotel_nombre.short_description = 'Hotel'

    def categoria_nombre(self, obj):
        return obj.ID_categoria.nombre
    categoria_nombre.admin_order_field = 'ID_categoria'
    categoria_nombre.short_description = 'Categoría'


# ========== SERVICIOS ==========
@admin.register(Servicios_Hoteles)
class ServiciosHotelesAdmin(admin.ModelAdmin):
    list_display = ['nombre_servicio']
    search_fields = ['nombre_servicio']

@admin.register(Hoteles_Servicios)
class HotelServicioAdmin(admin.ModelAdmin):
    list_display = ['hotel', 'servicio_hotel']
    #list_filter = ['ID_hotel', 'ID_servicio_hotel']

    def hotel_nombre(self, obj):
        return obj.ID_hotel.nombre

    def servicio_nombre(self, obj):
        return obj.ID_servicio_hotel.nombre 

    hotel_nombre.admin_order_field = 'ID_hotel'
    servicio_nombre.admin_order_field = 'ID_servicio_hotel'
    hotel_nombre.short_description = 'Hotel'
    servicio_nombre.short_description = 'Servicio'


@admin.register(Servicios_Categorias_Habitaciones)
class ServicioCategoriaHabitacionAdmin(admin.ModelAdmin):
    list_display = ['nombre_servicio']

    def servicio_nombre(self, obj):
        return obj.ID_servicio_hotel.nombre_servicio
    servicio_nombre.admin_order_field = 'ID_servicio_hotel__nombre_servicio'  # para ordenar
    servicio_nombre.short_description = 'Servicio'

    def categoria_nombre(self, obj):
        return str(obj.ID_categoria)
    categoria_nombre.admin_order_field = 'ID_categoria'
    categoria_nombre.short_description = 'Categoría'

    search_fields = ['ID_servicio_hotel__nombre_servicio', 'ID_categoria__nombre_categoria']


@admin.register(Categorias_Servicios)
class CategoriasServiciosAdmin(admin.ModelAdmin):
    list_display = ['servicio_hotel', 'categoria']
    ##list_filter = ['ID_categoria', 'ID_servicio_hotel']

    def categoria(self, obj):
        return obj.ID_categoria.nombre_categoria
    categoria.admin_order_field = 'ID_categoria'
    categoria.short_description = 'Categoría'

    def servicio(self, obj):
        return obj.ID_servicio_hotel.nombre
    servicio.admin_order_field = 'ID_servicio_hotel'
    servicio.short_description = 'Servicio'


# ========== DISPONIBILIDAD ==========
@admin.register(Disponibilidad_Categorias)
class DisponibilidadCategoriaAdmin(admin.ModelAdmin):
    list_display = ['categoria_nombre', 'fecha', 'cantidad_disponible']
    #list_filter = ['ID_categoria', 'fecha']

    def categoria_nombre(self, obj):
        return obj.ID_categoria.nombre

    categoria_nombre.admin_order_field = 'ID_categoria'  
    categoria_nombre.short_description = 'Categoría'




# ========== RESERVAS ==========
@admin.register(Estados_Reservas)
class EstadosReservasAdmin(admin.ModelAdmin):
    list_display = ['descripcion_estado_reserva']

    def id_estado(self, obj):
        return obj.ID_estado_reserva
    id_estado.admin_order_field = 'ID_estado_reserva'  # para ordenar

    def descripcion(self, obj):
        return obj.descripcion_estado_reserva
    descripcion.admin_order_field = 'descripcion_estado_reserva'

    search_fields = ['descripcion_estado_reserva']



@admin.register(Reservas_Hoteles)
class ReservasHotelesAdmin(admin.ModelAdmin):
    list_display = ['monto_total_hotel', 'fecha_reserva', 'viajero','fecha_ingreso','fecha_egreso','estado_reserva']
    ##list_filter = ['ID_estado_reserva', 'fecha_reserva']
    ##search_fields = ['ID_viajero__nombre', 'ID_viajero__apellido']

    def get_viajero(self, obj):
        return f"{obj.ID_viajero.nombre} {obj.ID_viajero.apellido}"
    get_viajero.short_description = 'Viajero'
    get_viajero.admin_order_field = 'ID_viajero__nombre'

    def get_estado(self, obj):
        return obj.ID_estado_reserva.descripcion_estado_reserva if obj.ID_estado_reserva else '-'
    get_estado.short_description = 'Estado'
    get_estado.admin_order_field = 'ID_estado_reserva__descripcion_estado_reserva'



@admin.register(Reservas_Hoteles_Detalles)
class ReservasHotelesDetallesAdmin(admin.ModelAdmin):
    list_display = ['reserva', 'categoria', 'cantidad_habitaciones', 'precio_unitario', 'sub_total']
    #list_filter = ['ID_categoria']

    def reserva(self, obj): 
        return str(obj.ID_reserva_hotel)
    reserva.admin_order_field = 'ID_reserva_hotel'
    reserva.short_description = 'Reserva'

    def categoria(self, obj):
        return str(obj.ID_categoria)
    categoria.admin_order_field = 'ID_categoria'
    categoria.short_description = 'Categoría'

