from django.db import connection
from django.db import connection, DatabaseError


def obtenerHoteles():
    with connection.cursor() as cursor:
        cursor.execute("EXEC obtenerHoteles")
        columnas = [col[0] for col in cursor.description]
        return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]

def buscarHotel(id_direccion, tipo):
    with connection.cursor() as cursor:
        cursor.execute("EXEC buscarHotel %s, %s", [id_direccion, tipo])
        filas = cursor.fetchall()
        
        if not filas:
            return []  # No hay datos

        columnas = [col[0] for col in cursor.description]
        resultados = [dict(zip(columnas, fila)) for fila in filas]
        return resultados
    
def buscarHotelPorId(id_hotel):
    with connection.cursor() as cursor:
        cursor.execute("EXEC buscarHotelPorId %s", [id_hotel])
        filas = cursor.fetchall()
        columnas = [col[0] for col in cursor.description]
        resultados = [dict(zip(columnas, fila)) for fila in filas]
        return resultados

def mostrarHabitacionesHotel(id_hotel, fecha_ingreso, fecha_egreso):
    with connection.cursor() as cursor:
        cursor.execute("EXEC buscarHabitacionesDisponibles %s, %s, %s", [id_hotel, fecha_ingreso, fecha_egreso])
        columnas = [col[0] for col in cursor.description]
        return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]

def mostrarServiciosHotel(id_hotel):
    with connection.cursor() as cursor:
        cursor.execute("EXEC mostrarServiciosHotel %s", [id_hotel])
        columnas = [col[0] for col in cursor.description]
        resultados = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
        return resultados
    
def mostrarServiciosCategorias(id_categoria):
    with connection.cursor() as cursor:
        cursor.execute("EXEC mostrarServiciosCategorias %s", [id_categoria])
        columnas = [col[0] for col in cursor.description]
        resultados = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
        return resultados
    
def buscarCategoriaPorId(id_categoria):
    with connection.cursor() as cursor:
        cursor.execute("EXEC buscarCategoriaPorId %s", [id_categoria])
        columnas = [col[0] for col in cursor.description]
        resultados = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
        return resultados

def verificarOCrearDireccion(pais, provincia, localidad, calle, numero, cod_postal):
    with connection.cursor() as cursor:
        cursor.execute("EXEC verificarOCrearDireccion %s, %s, %s, %s, %s, %s", 
                       [pais, provincia, localidad, calle, numero, cod_postal])
        row = cursor.fetchone()
        return row[0] if row else None  # Devuelve solo el ID o None

def ingresarDatos(identificacion, nombre, apellido, telefono, email, fecha_nacimiento, clave, direccion_id):
    with connection.cursor() as cursor:
        cursor.execute("EXEC ingresarDatos %s, %s, %s, %s, %s, %s, %s, %s", 
                       [identificacion, nombre, apellido, telefono, email, fecha_nacimiento, clave, direccion_id])
        row = cursor.fetchone()
        return row[0] if row else None

def insertarCabeceraReservaHotel(monto_total,fecha_reserva,fecha_ingreso,fecha_egreso,estado_reserva_id,viajero_id,hotel_id):
    with connection.cursor() as cursor:
        cursor.execute("EXEC insertarCabeceraReservaHotel %s, %s, %s, %s, %s, %s,%s", 
                       [monto_total,fecha_reserva,fecha_ingreso,fecha_egreso,estado_reserva_id,viajero_id,hotel_id])
        row = cursor.fetchone()
        return row[0] if row else None  # Devuelve solo el ID o None

def insertarDetalleReservaHotel(cantidad_habitaciones,precio_unitario,sub_total,categoria_id,reserva_hotel_id):
    with connection.cursor() as cursor:
        cursor.execute("EXEC insertarDetalleReservaHotel %s, %s, %s, %s, %s", 
                       [cantidad_habitaciones,precio_unitario,sub_total,categoria_id,reserva_hotel_id])

def generarFactura(id_reserva):
    resultados = {
        'viajero': [],
        'reserva': [],
        'hotel': [],
        'detalle': []
    }

    with connection.cursor() as cursor:
        cursor.execute("EXEC generarFactura %s", [id_reserva])

        #  Datos del viajero
        columnas = [col[0] for col in cursor.description]
        resultados['viajero'] = [dict(zip(columnas, row)) for row in cursor.fetchall()]

        #  Datos de la cabecera de la reserva
        cursor.nextset()
        columnas = [col[0] for col in cursor.description]
        resultados['reserva'] = [dict(zip(columnas, row)) for row in cursor.fetchall()]

        # Datos del hotel
        cursor.nextset()
        columnas = [col[0] for col in cursor.description]
        resultados['hotel'] = [dict(zip(columnas, row)) for row in cursor.fetchall()]

        # Datos del detalle de reserva
        cursor.nextset()
        columnas = [col[0] for col in cursor.description]
        resultados['detalle'] = [dict(zip(columnas, row)) for row in cursor.fetchall()]

    return resultados

def obtenerReservas(id_viajero):
    with connection.cursor() as cursor:
        cursor.execute("EXEC obtenerReservas %s", [id_viajero])
        columnas = [col[0] for col in cursor.description]
        return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
      
def cancelarReserva(id_reserva):
    try:
        with connection.cursor() as cursor:
            cursor.execute("EXEC cancelarReserva %s", [id_reserva])
    except DatabaseError as e:
        raise Exception("No se pudo cancelar la reserva: " + str(e))
     
def mostrarDetalleReserva(id_reserva):
    resultados = {
        'viajero': [],
        'reserva': [],
        'hotel': [],
        'detalle': []
    }

    with connection.cursor() as cursor:
        cursor.execute("EXEC generarFactura %s", [id_reserva])

        #  Datos del viajero
        columnas = [col[0] for col in cursor.description]
        resultados['viajero'] = [dict(zip(columnas, row)) for row in cursor.fetchall()]

        #  Datos de la cabecera de la reserva
        cursor.nextset()
        columnas = [col[0] for col in cursor.description]
        resultados['reserva'] = [dict(zip(columnas, row)) for row in cursor.fetchall()]

        # Datos del hotel
        cursor.nextset()
        columnas = [col[0] for col in cursor.description]
        resultados['hotel'] = [dict(zip(columnas, row)) for row in cursor.fetchall()]

        # Datos del detalle de reserva
        cursor.nextset()
        columnas = [col[0] for col in cursor.description]
        resultados['detalle'] = [dict(zip(columnas, row)) for row in cursor.fetchall()]

    return resultados

def generarComprobanteCancelacion(id_reserva):
     with connection.cursor() as cursor:
        cursor.execute("EXEC generarComprobanteCancelacion %s", [id_reserva])
        columnas = [col[0] for col in cursor.description]
        return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]