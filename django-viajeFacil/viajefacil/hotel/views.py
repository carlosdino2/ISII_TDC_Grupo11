from django.shortcuts import render,redirect
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Hotel, Localidad
from django.db import connection
from datetime import datetime
import locale
from decimal import Decimal, ROUND_HALF_UP
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.template.loader import get_template
from itertools import combinations_with_replacement
from .utils import obtenerHoteles,buscarHotel,mostrarHabitacionesHotel,mostrarServiciosHotel,mostrarServiciosCategorias,buscarHotelPorId,ingresarDatos
from .utils import verificarOCrearDireccion,ingresarDatos,insertarCabeceraReservaHotel,insertarDetalleReservaHotel,generarFactura,obtenerReservas
from .utils import cancelarReserva,generarComprobanteCancelacion

def index_alojamientos (request):
    return render (request, 'index_alojamientos.html')

def lista_hoteles(request):
    hoteles = Hotel.objects.prefetch_related('categorias_hotel__categoria')  # prefetch de relación M2M
    return render(request, 'lista_hoteles.html', {'hoteles': hoteles})

def obtener_destinos(request):
    localidades = Localidad.objects.select_related('provincia__pais').all()

    destinos = []
    for loc in localidades:
        destinos.append({
            'destino': f"{loc.nombre_localidad}, {loc.provincia.nombre_provincia}, {loc.provincia.pais.nombre_pais}",
            'tipo': 'localidad',
            'id': loc.id
        })

    return JsonResponse(destinos, safe=False)

def index_alojamientos(request):
    hoteles_lista = obtenerHoteles()
    paginator = Paginator(hoteles_lista, 2)  #2 hoteles por página

    page_number = request.GET.get('page')  # página actual
    hoteles = paginator.get_page(page_number)

    return render(request, 'index_alojamientos.html', {
        'hoteles': hoteles
    })

def buscar_destinos(request):
    termino = request.GET.get('term', '')

    resultados = []
    if termino:
        with connection.cursor() as cursor:
            cursor.execute("EXEC busquedaDestinos %s", [termino])
            for row in cursor.fetchall():
                resultados.append({
                    'destino': row[0],  # texto visible
                    'tipo': row[1],     # 'provincia' o 'localidad'
                    'id': row[2]        # ID
                })

    return JsonResponse(resultados, safe=False)

def alojamientos(request):
    tipo = request.GET.get("tipo")
    id_origen = request.GET.get("id")

    hoteles = []
    if tipo and id_origen:
        try:
            hoteles = buscarHotel(id_origen,tipo)
        except Exception as e:
            print(f"Error al buscar hoteles: {e}")
            hoteles = []

    paginator = Paginator(hoteles, 3)
    page_number = request.GET.get('page')
    hoteles_paginados = paginator.get_page(page_number)

    return render(request, 'index_alojamientos.html', {
        'hoteles': hoteles_paginados
    })

def hoteles_por_destino(request):

    # Guardamos los datos de búsqueda en sesión
    request.session['busqueda'] = {
    'fecha_ingreso': request.GET.get('fecha_ingreso'),  
    'fecha_egreso': request.GET.get('fecha_salida'),   
    'cantidad_personas': request.GET.get('cantidad_personas'),
    'cantidad_habitaciones': request.GET.get('cantidad_habitaciones'),
    }

    tipo = request.GET.get('tipo')
    id_origen = request.GET.get('id')

    hoteles = []
    error = None

    if tipo and id_origen:
            hoteles = buscarHotel(id_origen, tipo)

    if not hoteles:
        error = "No se encontraron hoteles para el destino seleccionado"


    return render(request, 'lista_hoteles.html', {
        'hoteles': hoteles,
        'error': error
    })

def generar_combinaciones_validas(categorias, personas, habitaciones_max):
    combinaciones_validas = []

    # Extraemos solo las categorías con al menos una disponibilidad
    categorias_disponibles = [
        cat for cat in categorias if cat['cantidad_disponible'] > 0
    ]

    for r in range(1, habitaciones_max + 1):  # cantidad de habitaciones desde 1 hasta habitaciones_max
        for combo in combinations_with_replacement(categorias_disponibles, r):
            total_personas = sum(cat['capacidad_categoria'] for cat in combo)
            cantidad_por_categoria = {}
            for cat in combo:
                key = cat['id_categoria']
                cantidad_por_categoria[key] = cantidad_por_categoria.get(key, 0) + 1

            # Validar si hay disponibilidad real y se cubren las personas
            if total_personas >= personas and all(
                cantidad_por_categoria[key] <= next(
                    (c['cantidad_disponible'] for c in categorias_disponibles if c['id_categoria'] == key), 0
                ) for key in cantidad_por_categoria
            ):
                combinaciones_validas.append(combo)

    return combinaciones_validas

def obtener_entero_seguro(valor, por_defecto=1):
    try:
        return int(valor)
    except (ValueError, TypeError):
        return por_defecto

def detalle_hotel(request, id):
   #Obtenemos los datos de la sesion
    datos = request.session.get('busqueda')
    #Obtenemos las fechas
    fecha_ingreso = datos.get('fecha_ingreso')  # '2025-06-23'
    fecha_egreso = datos.get('fecha_egreso')    # '2025-06-29'
    
    hoteles = buscarHotel(id, 'localidad')
    hotel = hoteles[0] if hoteles else None

    if hotel:
        request.session['id_hotel'] = id
        categorias = mostrarHabitacionesHotel(hotel['id'], fecha_ingreso, fecha_egreso)

        for cat in categorias:
            id_cat = cat.get('id_categoria')
            cat['servicios'] = mostrarServiciosCategorias(id_cat)

        servicios = mostrarServiciosHotel(hotel['id'])

        # Recuperar los datos del formulario (personas y habitaciones)
        datos_busqueda = request.session.get('busqueda', {})
        personas = obtener_entero_seguro(datos_busqueda.get('cantidad_personas'), 1)
        habitaciones = obtener_entero_seguro(datos_busqueda.get('cantidad_habitaciones'), 1)


        # Generar combinaciones válidas
        combinaciones = generar_combinaciones_validas(categorias, personas, habitaciones)
        combinaciones = [list(tupla) for tupla in combinaciones]
        request.session['combinaciones'] = combinaciones


        print("",combinaciones),
        return render(request, 'detalle_hotel.html', {
            'hotel': hotel,
            'categorias': categorias,
            'servicios': servicios,
            'combinaciones': combinaciones,
            'personas': personas,
            'habitaciones': habitaciones,
        })
    

    return render(request, 'detalle_hotel.html', {
        'error': "No se encontró el hotel solicitado"
    })

def seleccionar_categoria(request):
    if request.method == 'POST':
        id_categoria = request.POST.get('id_categoria')
        if id_categoria:
            request.session['id_categoria_seleccionada'] = id_categoria
            return redirect('hotel:detalle_reserva')  # va al finalizar reserva
    return redirect('hotel:buscar_alojamientos')  # redirige si falla

def calcular_dias_reserva(request):
    #Obtenemos los datos de la sesion
    datos = request.session.get('busqueda')
    #Obtenemos las fechas
    fecha_ingreso_str = datos.get('fecha_ingreso')  # '2025-06-23'
    fecha_egreso_str = datos.get('fecha_egreso')    # '2025-06-29'

    try:
        fecha_ingreso = datetime.strptime(fecha_ingreso_str, '%Y-%m-%d')
        fecha_egreso = datetime.strptime(fecha_egreso_str, '%Y-%m-%d')
    except Exception as e:
        print("Error al convertir fechas:", e)
        fecha_ingreso = fecha_egreso = None

    # Validamos fechas antes de restar
    if fecha_ingreso and fecha_egreso and fecha_egreso > fecha_ingreso:
        cantidad_noches = (fecha_egreso - fecha_ingreso).days
    else:
        cantidad_noches = 1

    return cantidad_noches

def detalle_reserva(request):
    locale.setlocale(locale.LC_TIME, 'Spanish_Argentina')

    datos = request.session.get('busqueda')
    id_hotel = request.session.get('id_hotel')
    hotel = buscarHotelPorId(id_hotel)
    cantidad_noches = calcular_dias_reserva(request)

    fecha_ingreso = datetime.strptime(datos.get('fecha_ingreso'), '%Y-%m-%d')
    fecha_egreso = datetime.strptime(datos.get('fecha_egreso'), '%Y-%m-%d')

    fecha_ingreso_fmt = fecha_ingreso.strftime('%a. %d %b. %Y').capitalize()
    fecha_egreso_fmt = fecha_egreso.strftime('%a. %d %b. %Y').capitalize()

    estrellas = range(hotel[0]['cantidad_estrellas_hotel'])

    # 💡 Obtener la combinación de habitaciones seleccionadas
    combinacion = request.session.get('combinacion_elegida', [])
    total_bruto = 0

    # Calcular el total sumando los precios de cada habitación x noches
    for hab in combinacion:
        precio_str = hab['precio_categoria'].replace('.', '').replace(',', '.')
        precio_unitario = float(precio_str)
        total_bruto += precio_unitario * cantidad_noches

    # 💰 Impuestos y cargos
    impuestos = total_bruto * 0.21
    cargos = total_bruto * 0.05
    total_final = total_bruto + impuestos + cargos

    request.session['precio_final'] = total_final
    personas = obtener_entero_seguro(datos.get('cantidad_personas'), 1)

    # 💸 Formato
    f = lambda x: f"{x:,.0f}".replace(",", ".")

    return render(request, 'index_reserva.html', {
        'datos': datos,
        'hotel': hotel[0],
        'estrellas': estrellas,
        'precio_reserva': f(total_bruto),
        'impuestos': f(impuestos),
        'cargos': f(cargos),
        'precio_final': f(total_final),
        'fecha_ingreso_fmt': fecha_ingreso_fmt,
        'fecha_egreso_fmt': fecha_egreso_fmt,
        'cantidad_noches': cantidad_noches,
        'combinacion': combinacion,
        'personas':personas
    })

def vista_registro(request):

    return render(request, 'index_register.html')

def generar_detalle_reserva(request):

    if request.method == 'POST':
        # Guardás en sesión (o podrías recibir desde POST también)
        detalle = calcular_detalle_desde_combinacion(request)

         # ESTE PRINT ES EL IMPORTANTE
        print("DETALLE DE RESERVA GENERADO:", detalle)

        request.session['detalle_reserva'] = detalle  # Guardar en sesión si hace falta
        return redirect('hotel:detalle_reserva')  # Redirige a la página de confirmación
    else:
        return redirect('hotel:buscar_alojamientos')

def calcular_detalle_desde_combinacion(request):
    noches = calcular_dias_reserva(request)

    indice = int(request.POST.get('indice'))
    combinaciones = request.session.get('combinaciones', [])
    if not 0 <= indice < len(combinaciones):
        return []

    combinacion = combinaciones[indice]
    request.session['combinacion_elegida'] = combinacion

    detalle = []

    for habitacion in combinacion:
        cat_id = habitacion['id_categoria']
        precio_str = habitacion['precio_categoria'].replace('.', '').replace(',', '.')
        precio_unitario = float(precio_str)
        subtotal = precio_unitario * noches

        detalle.append({
            'categoria_id': cat_id,
            'precio_unitario': precio_unitario,
            'subtotal': subtotal
        })
    
    return detalle

#Desde aqui empiezan las funciones de la creacion de la reserva
#--
#--Funcion para registrar el viajero
def insertar_viajero(request):
    if request.method == 'POST':
        # Datos personales
        nombre = request.POST.get('nombre_viajero')
        apellido = request.POST.get('apellido_viajero')
        identificacion = request.POST.get('identificacion_viajero')
        email = request.POST.get('email_viajero')
        telefono = request.POST.get('telefono_viajero')
        nacimiento = request.POST.get('fecha_nacimiento_viajero')
        clave = 'NULL'

        # Dirección
        pais = request.POST.get('pais') or 'Argentina'
        provincia = request.POST.get('provincia')
        localidad = request.POST.get('localidad') 
        calle = request.POST.get('calle')
        numero = request.POST.get('numero')
        cod_postal = request.POST.get('codpostal')

        # Paso siguiente (cuando esté el proc): llamar a verificarOCrearDireccion
        id_direccion=verificarOCrearDireccion(pais,provincia,localidad,calle,numero,cod_postal)
        # y luego insertar el viajero
        id_viajero = ingresarDatos(identificacion,nombre,apellido,telefono,email,nacimiento,clave,id_direccion)
    return id_viajero

#--Funcion para generar la cabecera
def insertar_cabecera_reserva(request):
    # Obtenemos datos generales
    datos = request.session.get('busqueda')
    # Obtener datos de cabecera
    monto_total = request.session.get('precio_final', '0')
    
    #Obtenemos el id hotel
    hotel_id = request.session.get('id_hotel')
    
    # Estado: será 1 (Confirmada)
    estado_id = 1 
    #Fecha del dia de la reserva
    fecha_reserva = datetime.today().date()

    # Fechas
    fecha_ingreso = datos.get('fecha_ingreso')
    fecha_egreso = datos.get('fecha_egreso')
    fecha_reserva = datetime.today().date()

    id_viajero = request.session['id_viajero']

    #Generamos la cabecera de la reserva
    id_cabecera_reserva=insertarCabeceraReservaHotel(monto_total,fecha_reserva,fecha_ingreso,fecha_egreso,estado_id,id_viajero,hotel_id)
    
    #Devolvemos el id
    return id_cabecera_reserva

#--Funcion para insertar el detalle de la reserva del hotel

def insertar_detalle_reserva(request):
    if request.method == 'POST':
        reserva_id = request.session.get('id_reserva')
        combinacion = request.session.get('combinacion_elegida', [])

        noches = calcular_dias_reserva(request)
        detalle = []

        for habitacion in combinacion:
            cat_id = habitacion['id_categoria']
            precio_str = habitacion['precio_categoria'].replace('.', '').replace(',', '.')
            try:
                precio_unitario = float(precio_str)
            except Exception as e:
                print("⚠️ Error al convertir precio:", precio_str, e)
                continue

            subtotal = precio_unitario * noches

            detalle.append({
                'categoria_id': cat_id,
                'precio_unitario': precio_unitario,
                'subtotal': subtotal
            })

        for item in detalle:
            insertarDetalleReservaHotel(
                cantidad_habitaciones=1,
                precio_unitario=item['precio_unitario'],
                sub_total=item['subtotal'],
                categoria_id=item['categoria_id'],
                reserva_hotel_id=reserva_id,
            )

#--Funcion final, donde va ir si la reserva fue exitosa
def reserva_exitosa(request):
    return render(request,'reserva_exitosa.html')

# -- FUNCIÓN FINAL PARA REGISTRAR TODA LA RESERVA COMPLETA --
def procesar_reserva_completa(request):
    if request.method == 'POST':
        try:
            # 1. Registrar el viajero (y guardar su id en sesión)
            id_viajero = insertar_viajero(request)
            request.session['id_viajero'] = id_viajero

            # 2. Generar cabecera de reserva (y guardar su id en sesión)
            id_reserva = insertar_cabecera_reserva(request)
            request.session['id_reserva'] = id_reserva

            # 3. Insertar detalle (usando la combinación seleccionada y la reserva id)
            insertar_detalle_reserva(request)

            print("✅ Reserva registrada correctamente")
            return redirect('hotel:reserva_exitosa')

        except Exception as e:
            print("❌ Error al procesar reserva:", e)
            return redirect('hotel:detalle_reserva')

    return redirect('hotel:buscar_alojamientos')

def ver_factura(request, id_reserva):
    try:
        factura = generarFactura(id_reserva)

        # Extraer datos clave
        reserva = factura['reserva'][0]
        monto_total = reserva['monto_total_reserva']

        # Calcular componentes del total
        subtotal = (monto_total / Decimal('1.26')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        impuestos = (subtotal * Decimal('0.21')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        cargos = (subtotal * Decimal('0.05')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

        contexto = {
            'viajero': factura['viajero'][0],
            'reserva': reserva,
            'hotel': factura['hotel'][0],
            'detalle': factura['detalle'],
            'subtotal': subtotal,
            'impuestos': impuestos,
            'cargos': cargos,
        }
        
        email_viajero = "carlosdaniel313@gmail.com"
        enviar_factura_por_correo(request, id_reserva, email_viajero)


        return render(request, 'index_factura.html', contexto)

    except Exception as e:
        print(f"❌ Error al generar factura: {e}")
        return render(request, 'index_factura.html', {
            'error': 'No se pudo generar la factura.'
        })

def enviar_factura_por_correo(request, id_reserva, email_destino):
    try:
        factura = generarFactura(id_reserva)
        context = {
            'viajero': factura['viajero'][0],
            'reserva': factura['reserva'][0],
            'hotel': factura['hotel'][0],
            'detalle': factura['detalle'],
            'subtotal': factura.get('subtotal', 0),
            'impuestos': factura.get('impuestos', 0),
            'cargos': factura.get('cargos', 0),
        }

        html_content = render_to_string('index_factura.html', context)

        asunto = f"Factura de tu reserva #{context['reserva']['nro_reserva']}"
        mensaje = EmailMultiAlternatives(
            subject=asunto,
            body='Gracias por tu reserva. Adjunto encontrarás tu factura.',
            from_email='tucorreo@gmail.com',
            to=[email_destino]
        )
        mensaje.attach_alternative(html_content, "text/html")
        mensaje.send()

        print("📧 Factura enviada a", email_destino)

    except Exception as e:
        print("❌ Error al enviar el correo:", e)

def ver_reservas(request,id_viajero):

    try:
        reservas = obtenerReservas(id_viajero)
    except Exception as e:
        print("❌ Error al obtener reservas:", e)
        reservas = []

    return render(request, 'mis_reservas.html', {'reservas': reservas})

def cancelar_reserva(request):
    id_reserva = request.POST.get('id_reserva')
    id_viajero = request.POST.get('id_viajero')
    
    print("Id viajero",id_viajero) 

    if not id_reserva or not id_viajero:
        messages.error(request, "No se pudo cancelar la reserva. ID no válido.")
        return redirect('hotel:ver_reservas', id_viajero=1) 
    try:
        cancelarReserva(int(id_reserva))
        messages.success(request, "Cancelación Exitosa")
    except Exception as e:
        print(" Error al cancelar reserva:", e)
        messages.warning(request, "No se puede cancelar la reserva con menos de 2 días de anticipación.")

    return redirect('hotel:ver_reservas', id_viajero=id_viajero)

def detalle_reserva_hotel(request):
    
    id_reserva = request.POST.get('id_reserva')
    try:
        factura = generarFactura(id_reserva)

        # Extraer datos clave
        reserva = factura['reserva'][0]
        monto_total = reserva['monto_total_reserva']

        # Calcular componentes del total
        subtotal = (monto_total / Decimal('1.26')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        impuestos = (subtotal * Decimal('0.21')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        cargos = (subtotal * Decimal('0.05')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

        contexto = {
            'viajero': factura['viajero'][0],
            'reserva': reserva,
            'hotel': factura['hotel'][0],
            'detalle': factura['detalle'],
            'subtotal': subtotal,
            'impuestos': impuestos,
            'cargos': cargos,
        }
        
    
        return render(request, 'detalle_Reserva.html', contexto)

    except Exception as e:
        print(f"❌ Error al generar factura: {e}")
        return render(request, 'detalle_reserva.html', {
            'error': 'No se pudo generar la factura.'
        })

def generar_comprobante_cancelacion(request,):
    id_reserva = request.POST.get('id_reserva')
    comprobante = generarComprobanteCancelacion(id_reserva)
    print("COmprobante",comprobante)
    return render(request, 'comprobante_cancelacion.html', comprobante[0])