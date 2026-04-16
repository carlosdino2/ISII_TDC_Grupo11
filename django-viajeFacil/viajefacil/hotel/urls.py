from django.urls import path
from . import views

app_name= 'hotel'

urlpatterns = [
    path('alojamientos/', views.index_alojamientos, name='buscar_alojamientos'),
    path('lista_hoteles/', views.lista_hoteles, name='lista_hoteles'),
    path('api/destinos/', views.obtener_destinos, name='api_destinos'),  
    path('ajax/buscar-destinos/', views.buscar_destinos, name='ajax_buscar_destinos'),
    path('alojamientos/por-destino/', views.hoteles_por_destino, name='hoteles_por_destino'),
    path('detalle/<int:id>/', views.detalle_hotel, name='detalle_hotel'),
    path('seleccionar-categoria/', views.seleccionar_categoria, name='seleccionar_categoria'),
    path('reserva/', views.detalle_reserva, name='detalle_reserva'),
    path('register/', views.vista_registro, name='vista_registro'),
    path('reserva-exitosa/', views.reserva_exitosa, name='reserva_exitosa'),
    path('generar-detalle/', views.generar_detalle_reserva, name='generar_detalle_reserva'),
    path('confirmar-reserva/', views.procesar_reserva_completa, name='procesar_reserva'),
    path('factura/<int:id_reserva>/', views.ver_factura, name='ver_factura'),
    path('mis-reservas/<int:id_viajero>/', views.ver_reservas, name='ver_reservas'),
    path('cancelar-reserva/', views.cancelar_reserva, name='cancelar_reserva'),
    path('detalle-reserva/', views.detalle_reserva_hotel, name='detalle_reserva_hotel'),
    path('comprobante-cancelacion/', views.generar_comprobante_cancelacion, name='generar_comprobante_cancelacion'),
    
]
