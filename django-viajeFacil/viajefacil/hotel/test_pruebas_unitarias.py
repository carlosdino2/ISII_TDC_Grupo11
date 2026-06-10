from django.test import TestCase, Client
from unittest.mock import patch
from django.test import RequestFactory
from .views import verificarDatosViajero 

class pruebaUnitariaReservaVuelo(TestCase):

    def setUp(self):
        self.client = Client()
        session = self.client.session
        session['id_viajero'] = 1  
        session.save()
        
        # Datos base simulados del formulario para usar en las pruebas
        self.datos_formulario = {
            'nombre_viajero_1': 'Agustina',
            'apellido_viajero_1': 'Toledo',
            'dni_viajero_1': '451234567',
            'nac_viajero_1': '1998-10-15'
        }

    # ==========================================
    # PRUEBA 1: CASO FELIZ (Fila 1 de tu tabla)
    # ==========================================
    @patch('viajefacil.hotel.views.registrarPago')                 
    @patch('viajefacil.hotel.views.actualizarDisponibilidadVuelo') 
    @patch('viajefacil.hotel.views.reservarNuevoVuelo')            
    @patch('viajefacil.hotel.views.consultarCupo')                 
    @patch('viajefacil.hotel.views.verificarDatosTarjeta')         
    @patch('viajefacil.hotel.views.verificarDatosViajero')         
    def test_01_reservar_vuelo_datos_validos(self, mock_viajero, mock_tarjeta, mock_cupo, mock_reservar, mock_actualizar, mock_pago):
        print("\n==================================================")
        print("-> PRUEBA 1: Reserva normal con asientos disponibles")
        
        mock_viajero.return_value = 1
        mock_tarjeta.return_value = [{'ID_tarjeta': 123}]
        mock_cupo.return_value = [{'precio_clase': 50000.0}] 
        mock_reservar.return_value = [{'ID_reserva': 5001}] 
        mock_actualizar.return_value = True 
        mock_pago.return_value = [{'id_pago': 9999}] 

        # Parámetros de la Fila 1
        cant = 2
        id_clase = 1
        id_programacion_vuelo = 207
        url = f'/hotel/reserva-vuelo/{cant}/{id_clase}/{id_programacion_vuelo}/' 
        
        respuesta_vista = self.client.post(url, data=self.datos_formulario)
        
        # Verificamos que redirija al comprobante (302)
        self.assertEqual(respuesta_vista.status_code, 302)
        print("   [RESULTADO ESPERADO]: Reserva Exitosa (Retorna ID_reserva: 5001)")

    # ==========================================
    # PRUEBA 2: CUPO INSUFICIENTE (Fila 2)
    # ==========================================
    @patch('viajefacil.hotel.views.consultarCupo')                 
    @patch('viajefacil.hotel.views.verificarDatosTarjeta')         
    @patch('viajefacil.hotel.views.verificarDatosViajero') 
    def test_02_reservar_vuelo_cupo_insuficiente(self, mock_viajero, mock_tarjeta, mock_cupo):
        print("\n==================================================")
        print("-> PRUEBA 2: Solicitan más asientos de los disponibles")
        
        mock_viajero.return_value = 1
        mock_tarjeta.return_value = [{'ID_tarjeta': 123}]
        
        # Forzamos a que la base de datos tire error de cupo
        mock_cupo.side_effect = Exception("Cupo insuficiente")

        # Parámetros de la Fila 2
        cant = 100
        id_clase = 3
        id_programacion_vuelo = 206
        url = f'/hotel/reserva-vuelo/{cant}/{id_clase}/{id_programacion_vuelo}/' 
        
        respuesta_vista = self.client.post(url, data=self.datos_formulario)
        
        self.assertEqual(respuesta_vista.status_code, 302)
        print("   [RESULTADO ESPERADO]: Error - 'Cupo insuficiente'")

    # ==========================================
    # PRUEBA 3: ERROR DE TIPO (Fila 3)
    # ==========================================
    def test_03_reservar_vuelo_tipo_invalido(self):
        print("\n==================================================")
        print("-> PRUEBA 3: Parámetro de cantidad no es número entero")
        
        # Parámetros de la Fila 3
        cant = "dos"
        id_clase = 1
        id_programacion_vuelo = 206
        url = f'/hotel/reserva-vuelo/{cant}/{id_clase}/{id_programacion_vuelo}/' 
        
        respuesta_vista = self.client.post(url, data=self.datos_formulario)
        
        self.assertEqual(respuesta_vista.status_code, 404)
        print("   [RESULTADO ESPERADO]: Error de tipo - Parámetro inválido")

class TestRegistrarViajero(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    # ==========================================
    # PRUEBA 1: REGISTRO EXITOSO (Fila 1)
    # ==========================================
    @patch('viajefacil.hotel.views.registrarViajeroTemporal')
    @patch('viajefacil.hotel.views.verificarEmailViajero')
    def test_01_registro_exitoso(self, mock_verificar, mock_registrar):
        print("\n==================================================")
        print("-> PRUEBA 1: Registro de un viajero nuevo con email no existente")
        
        # 1. Simulamos que NO encuentra el email en la BD (devuelve lista vacía)
        mock_verificar.return_value = [] 
        # 2. Simulamos el registro devolviendo la estructura que espera tu [0].get()
        mock_registrar.return_value = [{'id_viajero': 8899}] 

        # 3. Armamos el POST con los datos desglosados de la Fila 1
        request = self.factory.post('/ruta-falsa/', {
            'email_contacto': 'carlos@gmail.com',
            'cod_area_contacto': '379',
            'telefono_contacto': '4001122' 
        })
        
        # Ejecutamos la función
        resultado = verificarDatosViajero(request)
        
        # Comprobamos que retornó el ID nuevo
        self.assertEqual(resultado, 8899)
        print(f"   [RESULTADO ESPERADO]: Registro Exitoso (Retorna ID_viajero único: {resultado}).")

    # ==========================================
    # PRUEBA 2: EMAIL YA REGISTRADO (Fila 2)
    # ==========================================
    @patch('viajefacil.hotel.views.registrarViajeroTemporal')
    @patch('viajefacil.hotel.views.verificarEmailViajero')
    def test_02_asociacion_exitosa(self, mock_verificar, mock_registrar):
        print("\n==================================================")
        print("-> PRUEBA 2: El email ya se encuentra registrado en el sistema")
        
        # 1. Simulamos que SÍ encuentra el email.
        mock_verificar.return_value = [{'ID_viajero': 105}] 
        
        request = self.factory.post('/ruta-falsa/', {
            'email_contacto': 'carlos@gmail.com',
            'cod_area_contacto': '379',
            'telefono_contacto': '4556677'
        })
        
        resultado = verificarDatosViajero(request)
        
        # Verificamos que devuelve el ID viejo y que NUNCA llamó a la función de registrar
        self.assertEqual(resultado, 105)
        mock_registrar.assert_not_called()
        print(f"   [RESULTADO ESPERADO]: Asociación Exitosa (Retornó ID existente {resultado} y no duplicó).")

    # ==========================================
    # PRUEBA 3: FORMATO INVÁLIDO (Fila 3)
    # ==========================================
    @patch('viajefacil.hotel.views.verificarEmailViajero')
    def test_03_email_invalido(self, mock_verificar):
        print("\n==================================================")
        print("-> PRUEBA 3: Parámetro incompleto o inválido")
        
        # simulamos ese error forzando un ValueError.
        mock_verificar.side_effect = ValueError("Parámetro inválido")
        
        request = self.factory.post('/ruta-falsa/', {
            'email_contacto': 'carlos.com', # Fila 3: Email sin arroba
            'cod_area_contacto': '379',
            'telefono_contacto': '515222'
        })
        
        # Comprobamos que el sistema levanta y frena por el ValueError
        with self.assertRaises(ValueError):
            verificarDatosViajero(request)
            
        print("   [RESULTADO ESPERADO]: Error de tipo (Parámetro inválido capturado correctamente).")