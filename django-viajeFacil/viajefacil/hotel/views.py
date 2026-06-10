from django.shortcuts import render,redirect
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Hotel, Localidad
from django.db import connection
from datetime import datetime
from django.utils.html import strip_tags
from django.conf import settings
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
from django.http import JsonResponse
from .models import Localidad
from django.utils import timezone
from django.shortcuts import render
from django.http import JsonResponse
from .utils import verificarRuta,buscarPorFecha,consultarCupo,obtenerVueloCheckout,verificarEmailViajero,registrarViajeroTemporal,verificarDatosTarjetaViajero
from .utils import reservarNuevoVuelo,actualizarDisponibilidadVuelo,registrarPago,generarComprobanteVuelo

#Modulo vuelos
def generarComprobanteReservaVuelo(request, id_pago):
    try:
        print(f"--> [VISTA COMPROBANTE] Iniciando carga para Pago N°: {id_pago}")
        
        # 1. Traemos la info de la BD
        resultado_raw = generarComprobanteVuelo(id_pago)

        # --- DESEMPAQUETADO CRÍTICO ---
        if isinstance(resultado_raw, list) and len(resultado_raw) > 0:
            datos_comprobante = resultado_raw[0]
        elif isinstance(resultado_raw, dict):
            datos_comprobante = resultado_raw
        else:
            datos_comprobante = None

        # Si vino completamente vacío, lanzamos el error
        if not datos_comprobante:
            raise Exception(f"No se encontraron registros válidos en la BD para el Pago N° {id_pago}")

        print(f"--> [DEBUG COMPROBANTE] Datos desempaquetados con éxito. Tipo: {type(datos_comprobante)}")

        # --- ENVÍO DE CORREO ELECTRÓNICO ---
        email_destino = datos_comprobante.get('email_viajero')
        print(email_destino)
        
        if email_destino:
            print(f"--> [CORREO] Preparando envío para: {email_destino}")
            
            # 1. Armamos el Asunto
            asunto = f"Confirmación de Reserva N° 000-{datos_comprobante.get('id_reserva')} - ViajeFácil"
            
            # 2. Renderizamos el HTML 
            html_content = render_to_string('reserva_exitosa.html', datos_comprobante)
            
            # 3. Creamos una versión en texto plano por si el correo del cliente no soporta HTML
            text_content = strip_tags(html_content)
            
            # 4. Configuramos el mensaje
            msg = EmailMultiAlternatives(
                subject=asunto,
                body=text_content,
                from_email=settings.EMAIL_HOST_USER,
                to=[email_destino]
            )
            
            # 5. Le adjuntamos  y enviamos
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            print("--> [CORREO] ¡Comprobante enviado con éxito!")

        # 4. Renderizamos la plantilla con la factura armada
        return render(request, 'reserva_exitosa.html', datos_comprobante)

    except Exception as e:
        print(f"--> [ERROR AL GENERAR COMPROBANTE]: {e}")
        return redirect('hotel:index_vuelos')

def reservarVuelo(request, cant, id_clase, id_programacion_vuelo):
    # Solo aceptamos que entren a esta función si apretaron el botón "Comprar"
    if request.method == 'POST':
        try:
            # 1. Capturamos la lista dinámica de pasajeros desde el formulario
            lista_pasajeros = []
            for i in range(1, cant + 1):
                pasajero = {
                    'nombre': request.POST.get(f'nombre_viajero_{i}', '').strip(),
                    'apellido': request.POST.get(f'apellido_viajero_{i}', '').strip(),
                    'dni': request.POST.get(f'dni_viajero_{i}', '').strip(),
                    'fecha_nac': request.POST.get(f'nac_viajero_{i}', '')
                }
                lista_pasajeros.append(pasajero)

            # 1.2. ALMACENAMIENTO TEMPORAL: Lo guardamos en la sesión de Django
            request.session['pasajeros_reserva_actual'] = lista_pasajeros
            
            # 1. Procesamos Viajero y Tarjeta con las funciones auxiliares
            id_viajero = verificarDatosViajero(request)
            id_tarjeta = verificarDatosTarjeta(request)

            # 2. Control de seguridad: Si falló la tarjeta, abortamos la reserva
            if not id_tarjeta:
                print("--> Abortando reserva: Hubo un error con la tarjeta.")
                # Redirigimos de vuelta al checkout original
                return redirect('hotel:checkout', cant=cant, id_clase=id_clase, id_programacion_vuelo=id_programacion_vuelo)

            # 3. Recalculamos el precio de forma segura en el backend
            cupos = consultarCupo(cant, id_clase, id_programacion_vuelo)
            precio_base = float(cupos[0].get('precio_clase'))
            detalle = calcular_costos_vuelo(precio_base,cant)
            monto_total_vuelo = detalle.get('precio_total')

            # 4. Impactamos la reserva en SQL Server
            fecha_reserva = datetime.now()
            # 4.1. ACOMODAMOS LA FECHA AL FORMATO ESTÁNDAR DE SQL SERVER
            fecha_reserva_limpia = fecha_reserva.strftime('%Y-%m-%d %H:%M:%S')

            id_reserva = reservarNuevoVuelo(fecha_reserva_limpia, monto_total_vuelo, cant, id_viajero, id_programacion_vuelo, id_clase)
            print(f"--> ¡Reserva generada con éxito! ID de Reserva: {id_reserva}")

            #5. Actualizamos la cantidad de asientos del vuelo:
            actualizarDisponibilidadVuelo(id_clase,id_programacion_vuelo,cant)

            # 5.1. DESEMPAQUETAMOS LOS IDS
            id_tarjeta_limpio = id_tarjeta[0].get('ID_tarjeta') if isinstance(id_tarjeta, list) and id_tarjeta else id_tarjeta
            id_reserva_limpio = id_reserva[0].get('ID_reserva') if isinstance(id_reserva, list) and id_reserva else id_reserva

            #6. Registramos el pago en la bd
            resultado_pago = registrarPago(fecha_reserva_limpia,monto_total_vuelo,id_tarjeta_limpio,id_reserva_limpio)

            # 6.1. DESEMPAQUETAMOS EL ID DE PAGO
            if isinstance(resultado_pago, list) and len(resultado_pago) > 0:
                id_pago_limpio = resultado_pago[0].get('id_pago')
            elif isinstance(resultado_pago, dict):
                id_pago_limpio = resultado_pago.get('id_pago')
            else:
                id_pago_limpio = resultado_pago

            #7.Redirigimos a la vista del comprobante
            return redirect('hotel:generarComprobanteReservaVuelo', id_pago=id_pago_limpio)
        #8. Devolvemos al checkout con el error
        except Exception as error_compra:
            print(f"--> [ERROR CRÍTICO EN FLUJO DE COMPRA]: {error_compra}")
            # Si algo falla, lo mandamos de vuelta al checkout avisando el motivo
            return redirect('hotel:checkout', cant=cant, id_clase=id_clase, id_programacion_vuelo=id_programacion_vuelo)

def verificarDatosTarjeta(request):
    #Obtenemos los datos de la tarjeta:
    num_tarjeta =str(request.POST.get('num_tarjeta', 0))
    titular_tarjeta = request.POST.get('titular_tarjeta',0)
    vencimiento_tarjeta = str(request.POST.get('venc_tarjeta',0))
    cod_seguridad_tarjeta = str(request.POST.get('cod_seguridad_tarjeta',0))
    dni_titular = str(request.POST.get('dni_titular',0))
   #verificamos los datos de la tarjeta, y si son correctos se insertan:
    id_tarjeta = verificarDatosTarjetaViajero(num_tarjeta,titular_tarjeta,vencimiento_tarjeta,cod_seguridad_tarjeta,dni_titular)
    if id_tarjeta:
        print("----------->Tarjeta aprobada!")
        return id_tarjeta
    else:
        print("----------->Error con la tarjeta!")
        return None

def verificarDatosViajero(request):
        #Obtenemos los datos de contacto del viajero
        email_contacto = str(request.POST.get('email_contacto', '')).strip()
        cod_Area = str(request.POST.get('cod_area_contacto', '')).strip()
        nro_contacto = str(request.POST.get('telefono_contacto', '')).strip()
        telefono_completo = cod_Area + nro_contacto

        #Verificamos si se encuentra registrado en nuestro sistema:
        ID_viajero_temporal= verificarEmailViajero(email_contacto);

        #Si el email ya se encuentra registrado:
        if ID_viajero_temporal:
         #Asociamos la reserva al ID del viajero
         print("--> Viajero existente encontrado.")
         #print(ID_viajero_temporal)
         return ID_viajero_temporal[0].get("ID_viajero")

        #Si *NO* se encuentra registrado:
        else:
            #Registramos al viajero temporalmente
            print("--> Viajero nuevo. Registrando temporalmente...")
            viajero_temporal = registrarViajeroTemporal(telefono_completo, email_contacto)
            #print(viajero_temporal[0].get('id_viajero'))
            return viajero_temporal[0].get("id_viajero")

def checkout(request,cant,id_clase,id_programacion_vuelo):

    #obtenemos el precio del vuelo seleccionado
    cupos= consultarCupo(cant, id_clase, id_programacion_vuelo);
    #obtenemos la info del vuelo (origen-destino-fecha de salida y hora)
    destinos = obtenerVueloCheckout(id_programacion_vuelo)
    #obtenemos el precio total del vuelo
    precio_total = float(cupos[0].get('precio_clase'))
    #obtenemos el detalle del costo del vuelo
    detalle = calcular_costos_vuelo(precio_total,cant)
    #mandamos a la vista
    return render(request, 'checkout-vuelo.html',{
        'cant':cant,
        'cantidad_pasajeros_loop': range(cant),
        'id_clase':id_clase,
        'id_programacion_vuelo':id_programacion_vuelo,
        'detalle':detalle,
        'destinos':destinos[0]
        })

def calcular_costos_vuelo(precio_total,cant_personas):
    # Definimos los porcentajes sobre el total
    porcentaje_base = 0.351 #35.1% precio del vuelo sin impuestos nacionales
    porcentaje_impuestos = 0.321 #32.1% impuestos
    porcentaje_tasas = 0.193 #19.3% tasas aeroportuarias
    porcentaje_cargos = 0.135 #13.5% cargos por servicios de ViajeFacil

    # Calculamos cada componente
    precio_base = round((precio_total * porcentaje_base)*cant_personas)
    impuestos = round((precio_total * porcentaje_impuestos)*cant_personas)
    tasas = round((precio_total * porcentaje_tasas)*cant_personas)
    cargos = round((precio_total * porcentaje_cargos)*cant_personas)

    total_extras = impuestos + tasas + cargos

    # Retornamos un diccionario con todo listo para la vista
    return {
        'precio_base': precio_base,
        'impuestos': impuestos,
        'tasas': tasas,
        'cargos': cargos,
        'total_extras': total_extras,
        'precio_total': precio_total*cant_personas
    }

def aplicarFiltrosResultados(lista_vuelos, criterio):
    if not lista_vuelos:
        return []

    if criterio == 'barato':
        # Ordenamos por el campo numérico precio_clase
        lista_vuelos.sort(key=lambda x: x['precio_unitario'])
    
    elif criterio == 'rapido':
        # Ordenamos por la duración de minutos para saber cual es el mas rapido
        lista_vuelos.sort(key=lambda x: x['duracion_minutos'])
    
    elif criterio == 'recomendado':
        # Ordenamos según la opción recomendado
        lista_vuelos.sort(key=lambda x: (x['precio_unitario'], x['duracion_minutos']))
        
    return lista_vuelos

def mostrarVuelosDisponibles(id_origen, id_destino, fecha, pasajeros, clase):
    #Creamos nuestra coleccion de vuelos vacía
    vuelos_encontrados = []
    #Pedimos las rutas para las localidades ingresadas
    rutas = verificarRuta(id_origen, id_destino)
    # Manejo de rutas nulas 
    cantidad_rutas = len(rutas) if rutas else 0
    print(f"--1: Rutas encontradas -> {cantidad_rutas}")
    #Si encontramos rutas entonces empezamos a armar los vuelos:
    if rutas:
        for vuelo_ruta in rutas:
            id_vuelo = vuelo_ruta['ID_vuelo']
            #Si existe la ruta entonces preguntamos si hay programaciones disponibles en las fechas ingresadas por el usuario:
            progs = buscarPorFecha(id_vuelo, fecha)
            cantidad_progs = len(progs) if progs else 0
            print(f"--2: Programaciones para Vuelo {id_vuelo} -> {cantidad_progs}") 
            #Si existen programaciones disponibles entonces preguntamos si existe cupo para la cantidad y clase que ingresó el usuario:
            if progs:
                for prog in progs:
                    id_prog = prog['ID_programacion_vuelo']
                    cupos = consultarCupo(pasajeros, clase, id_prog)
                    
                    if cupos:
                        print(f"--3: Cupo encontrado para Prog {id_prog}") 
                        
                        # Consolidación de datos
                        info_asiento = cupos[0] if isinstance(cupos, list) else cupos
                        #Armamos los datos para agregar a la lista de vuelos:
                        resultado_final = {
                            **vuelo_ruta,  
                            **prog,   
                            'cantidad_pasajeros':pasajeros, 
                            'id_programacion_vuelo':info_asiento.get('ID_programacion_vuelo'), 
                            'tipo_clase': info_asiento.get('descripcion_clase'),
                            'precio_unitario': info_asiento.get('precio_unitario'),
                            'precio_total': info_asiento.get('precio_total_formateado'),
                            'asientos_libres': info_asiento.get('asiento_disponible_clase'),
                            'cupo_info': info_asiento
                        }
                        #Creamos nuestra lista de vuelos:
                        vuelos_encontrados.append(resultado_final)

    # PRINT DE CONTROL FINAL
    print("\n" + "="*60)
    print(f"FINAL: {len(vuelos_encontrados)} vuelos enviados al front")
    print("="*60 + "\n")
    return vuelos_encontrados

def vuelos_disponibles(request):
    # 1. Obtención de datos
    try:
        id_origen = int(request.GET.get('id_origen', 0))
        id_destino = int(request.GET.get('id', 0))
        pasajeros = int(request.GET.get('cantidad_personas', 1))
        clase = int(request.GET.get('clase_vuelo', 1))
    except ValueError:
        return render(request, 'error.html', {'mensaje': 'Parámetros numéricos inválidos'})
    
    fecha = request.GET.get('fecha_ingreso')
    criterio_filtro = request.GET.get('orden', 'recomendado')
    error_sql = None
    vuelos_filtrados = []

    # 2. Validación 
    if not id_origen or not id_destino or not fecha:
        return render(request, 'lista_vuelos.html', {'vuelos': [], 'error_sql': "Faltan parámetros de búsqueda"})
    # 3. Logica de la busqueda
    try:
        # Consultamos los vuelos disponibles:
        vuelos = mostrarVuelosDisponibles(id_origen, id_destino, fecha, pasajeros, clase)
        # Aplicamos los filtros
        vuelos_filtrados = aplicarFiltrosResultados(vuelos, criterio_filtro)

    except Exception as e:
        error_sql = str(e)
        # Esto mostrará por consola el error exacto si algo falla
        print(f"ERROR CRÍTICO EN LA BÚSQUEDA: {error_sql}")
        
    # 4. Retornamos a la interfaz
    return render(request, 'lista_vuelos.html', {
        'vuelos': vuelos_filtrados,
        'orden_actual': criterio_filtro,
        'error_sql': error_sql
    })

def obtener_destinos_vuelos(request):
    # 1. Obtenemos el término que manda el fetch del JS (?term=...)
    termino = request.GET.get('term', '').strip()
    
    # 2. Si hay texto, filtramos. Si no, cortamos acá.
    if not termino:
        return JsonResponse([], safe=False)

    localidades = Localidad.objects.select_related('provincia__pais').filter(
        nombre_localidad__icontains=termino
    )[:10]

    # 4. Formateamos la salida
    resultados = []
    for loc in localidades:
        resultados.append({
            'id': loc.id_localidad,
            'destino': f"{loc.nombre_localidad}, {loc.provincia.nombre_provincia}, Argentina",
            'tipo': 'localidad'
        })
    
    return JsonResponse(resultados, safe=False)

def api_destinos(request):
    # 1. Capturamos lo que el usuario escribió 
    termino = request.GET.get('term', '').strip()
    

    # 2. Si hay menos de 2 letras, no buscamos nada (evita procesar de más)
    if len(termino) < 2:
        return JsonResponse([], safe=False)

    # 3. Aplicamos el filtro clave: __icontains 
    # Usamos select_related para traer la provincia de una sola vez
    query = Localidad.objects.select_related('provincia').filter(
        nombre_localidad__icontains=termino
    )[:10] # Limitamos a 10 resultados para que la lista no sea gigante

    # 4. Construimos la lista de diccionarios
    resultados = []
    for loc in query:
        resultados.append({
            'id': loc.id_localidad,
            'destino': f"{loc.nombre_localidad}, {loc.provincia.nombre_provincia}, Argentina",
            'tipo': 'localidad'
        })

    return JsonResponse(resultados, safe=False)

def index_vuelos(request):
    return render(request,'index_vuelos.html')

#Modulo hoteles
def index_alojamientos (request):
    return render (request, 'index_alojamientos.html')

def lista_hoteles(request):
    hoteles = Hotel.objects.prefetch_related('categorias_hotel__categoria')  # prefetch de relación M2M
    return render(request, 'lista_hoteles.html', {'hoteles': hoteles})

def obtener_destinos(request):
    localidades = Localidad.objects.select_related('provincia__pais').all()

    destinos = []
    print(localidades.query)
    for loc in localidades:
        destinos.append({
            'destino': f"{loc.nombre_localidad}, {loc.provincia.nombre_provincia}, {loc.provincia.pais.nombre_pais}",
            'tipo': 'localidad',
            'id': loc.id_localidad
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

    #  Formato
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