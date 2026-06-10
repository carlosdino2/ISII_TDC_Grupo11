-- Procedimiento para el autocompletado en la búsqueda de vuelos
CREATE PROCEDURE busquedaDestinosVuelos
    @termino NVARCHAR(100)
AS
BEGIN
    SET NOCOUNT ON;
    -- Solo mostrar resultados por localidad
    SELECT 
        CONCAT(l.nombre_localidad, ', ', p.nombre_provincia, ', ', pa.nombre_pais) AS destino,
        'localidad' AS tipo,
        l.ID_localidad AS id
    FROM Localidades l
    INNER JOIN Provincias p ON l.ID_provincia = p.ID_provincia
    INNER JOIN Paises pa ON p.ID_pais = pa.ID_pais
    WHERE l.nombre_localidad COLLATE Latin1_General_CI_AI LIKE '%' + @termino + '%'
    ORDER BY destino;
END

/*Procedimiento para verificar si existe una ruta entre dos lugares (Ej. Ctes -> Bariloche)
En el caso que exista, devuelve los vuelos entre esos dos lugares, si no, devuelve vacio.*/
CREATE PROCEDURE verificarRuta
    @id_localidad_origen INT,
    @id_localidad_destino INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT 
	--Datos del vuelo:
	ID_vuelo, numero_vuelo,duracion_estimada,v.ID_aerolinea,aero.nombre_aerolinea,		
	--Datos del del origen:
	origen_ID_aeropuerto,
	ao.nombre_completo as aeropuerto_origen,
	lo.ID_localidad as ID_localidad_origen, 
	lo.nombre_localidad AS origen_nombre,

	po.ID_provincia as ID_provincia_origen,
	po.nombre_provincia as provincia_origen,
	--Datos del destino:
	destino_ID_aeropuerto,
	ad.nombre_completo as aeropuerto_destino,
	ld.ID_localidad as ID_localidad_destino,
    ld.nombre_localidad AS destino_nombre,
	pd.ID_provincia as ID_provincia_destino,
	pd.nombre_provincia as provincia_destino

	FROM Vuelos v
	--Aerolinea:
	INNER JOIN Aerolineas aero ON v.ID_aerolinea = aero.ID_aerolinea
	--Origen:
	INNER JOIN Aeropuertos ao ON v.origen_ID_aeropuerto = ao.ID_aeropuerto
    INNER JOIN Direcciones dao ON ao.ID_direccion = dao.ID_direccion
    INNER JOIN Localidades lo ON dao.ID_localidad = lo.ID_localidad
	INNER JOIN Provincias po on lo.ID_provincia = po.ID_provincia
    --Destino:
    INNER JOIN Aeropuertos ad ON v.destino_ID_aeropuerto = ad.ID_aeropuerto
    INNER JOIN Direcciones dad ON ad.ID_direccion = dad.ID_direccion
    INNER JOIN Localidades ld ON dad.ID_localidad = ld.ID_localidad
	INNER JOIN Provincias pd on ld.ID_provincia = pd.ID_provincia
	WHERE  lo.ID_localidad = @id_localidad_origen and ld.ID_localidad = @id_localidad_destino

END
/*
Caso valido: (Ctes->Brc)
exec verificarRuta 11,9
Caso no valido: (No existe provincia con ID 20 -> Brc)
exec verificarRuta 20,9
*/
/*Procedimiento para verificar la programación de una ruta en un rango de fechas (Ej. Viaje de Ctes a Brc el 22/04/2026 y llegada el 26/04/2026)
Si existe, devuelve la programacion, si no, devuelve vacio*/
CREATE PROCEDURE buscarPorFecha
	@ID_vuelo INT,
    @fecha_salida DATETIME
AS
BEGIN
    SET NOCOUNT ON;
    SELECT 
	--Datos de la programacion de la ruta:
	ID_programacion_vuelo, fecha_salida, fecha_llegada, asientos_disponibles, 
	--Estado del vuelo: (Programado, A tiempo, Demorado, Suspendido, etc...)
	ev.descripcion_estado_vuelo,
	-- FECHA Y HORA DE SALIDA
        FORMAT(pv.fecha_salida, 'dd ''de'' MMMM ''de'' yyyy', 'es-AR') AS fecha_formateada,
        FORMAT(pv.fecha_salida, 'HH:mm') AS hora_salida,

        -- HORA DE LLEGADA
        FORMAT(pv.fecha_llegada, 'HH:mm') AS hora_llegada,

        -- DURACIÓN ESTIMADA
        -- Calculamos la diferencia en minutos y la formateamos como "X h Y m"
        CONCAT(
            DATEDIFF(MINUTE, pv.fecha_salida, pv.fecha_llegada) / 60, ' h ',
            DATEDIFF(MINUTE, pv.fecha_salida, pv.fecha_llegada) % 60, ' m'
        ) AS duracion_estimada,
		--DURACIÓN EN MINUTOS (PARA FILTRO)
		DATEDIFF(MINUTE, pv.fecha_salida, pv.fecha_llegada) AS duracion_minutos
	FROM Programacion_Vuelos pv
	INNER JOIN Estados_Vuelos ev on pv.ID_estado_vuelo = ev.ID_estado_vuelo
	WHERE pv.ID_vuelo = @ID_vuelo
	AND CAST(pv.fecha_salida AS DATE) = CAST(@fecha_salida AS DATE)
	AND pv.fecha_llegada >= pv.fecha_salida
END
/*
Caso valido: (Ctes->Brc salida: 22/04/2026 llegada: 22/04/2026)
exec buscarPorFecha 7,'2026-04-22 19:00'
Caso no valido: (Ctes->Brc salida: 23/04/2026 llegada: 22/04/2026 NO ES VALIDO NO PUEDE LLEGAR ANTES DE SALIR)
exec buscarPorFecha 7,'2026-04-23 19:00'
Caso no valido: (Ctes->Brc NO HAY VUELOS CARGADOS PARA ESA HORA)
exec buscarPorFecha 6,'2026-04-22 23:00'
Caso valido: (Si existe vuelo para esa hora)
exec buscarPorFecha 6,'2026-04-22 20:00'
*/
/*Procedimiento para consultar si hay asientos disponibles de la clase pedida en la programación (Ej. 2 asientos Economica)
Si hay asientos disponibles, devuelve la programación disponible, si no, devuelve vacio*/
CREATE PROCEDURE consultarCupo
	@cant INT,
	@ID_clase INT,
	@ID_programacion_vuelo INT
AS
	BEGIN
	SET NOCOUNT ON;
	SELECT *, c.descripcion_clase as tipo_clase,
	 -- PRECIOS
        FORMAT(pvc.precio_clase, 'C0', 'es-AR') AS precio_unitario,
        FORMAT(pvc.precio_clase * @cant, 'C0', 'es-AR') AS precio_total_formateado
	FROM Programaciones_Vuelos_Clases pvc
	INNER JOIN Clases c on pvc.ID_clase = c.ID_clase
	WHERE  pvc.ID_programacion_vuelo = @ID_programacion_vuelo
	AND pvc.asiento_disponible_clase >= @cant
	AND pvc.ID_clase = @ID_clase
END
/*
--Caso valido:
exec consultarCupo 10,1,206
--Caso no valido: Solo hay 22 asientos de clase 2 en la programacion 206
exec consultarCupo 30,2,206
*/
/*Procedimiento para traer los datos del vuelo para el checkout*/
CREATE PROCEDURE obtenerVueloCheckout
	@ID_programacion_vuelo INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT 
	--ID vuelo
	pv.ID_vuelo,
	-- FECHA Y HORA DE SALIDA
		FORMAT(pv.fecha_salida, 'ddd dd MMM yyyy', 'es-ES')AS fecha_salida,
        FORMAT(pv.fecha_salida, 'HH:mm') AS hora_salida,

		--Datos del del origen:
	lo.nombre_localidad AS origen_nombre,

	po.nombre_provincia as provincia_origen,
	--Datos del destino:
    ld.nombre_localidad AS destino_nombre,
	pd.nombre_provincia as provincia_destino

	FROM Programacion_Vuelos pv
	INNER JOIN Vuelos v on pv.ID_vuelo = v.ID_vuelo
	--Origen:
	INNER JOIN Aeropuertos ao ON v.origen_ID_aeropuerto = ao.ID_aeropuerto
    INNER JOIN Direcciones dao ON ao.ID_direccion = dao.ID_direccion
    INNER JOIN Localidades lo ON dao.ID_localidad = lo.ID_localidad
	INNER JOIN Provincias po on lo.ID_provincia = po.ID_provincia
    --Destino:
    INNER JOIN Aeropuertos ad ON v.destino_ID_aeropuerto = ad.ID_aeropuerto
    INNER JOIN Direcciones dad ON ad.ID_direccion = dad.ID_direccion
    INNER JOIN Localidades ld ON dad.ID_localidad = ld.ID_localidad
	INNER JOIN Provincias pd on ld.ID_provincia = pd.ID_provincia
	WHERE pv.ID_programacion_vuelo = @ID_programacion_vuelo
END
/*
--Caso valido:
exec obtenerVueloCheckout 206
--Caso no valido: no existe la programacion vuelo nro 500000
exec obtenerVueloCheckout 500000
*/
/*Procedimiento para traer los datos del vuelo para el checkout*/
CREATE PROCEDURE verificarEmailViajero
	@email NVARCHAR(200)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT 
	v.ID_viajero
	FROM Viajeros v
	WHERE v.email_viajero = @email
END
/*Caso valido: devuelve el id del viajero registrado en el sistema
exec verificarDatosViajero 'carlosdaniel313@gmail.com'
Caso no valido: No devuelve nada 
exec verificarDatosViajero 'carlosdaniel33@gmail.com'
*/
--Procedimiento para insertar viajero si no está registrado
CREATE PROCEDURE registrarViajeroTemporal
    @tel_viajero NVARCHAR(20),
    @email_viajero NVARCHAR(254)
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @nuevo_id INT;

    BEGIN TRY
        -- Iniciamos transacción con aislamiento estricto para evitar IDs duplicados en simultáneo
        BEGIN TRANSACTION;

        -- Calculamos el ID asegurando el bloqueo momentáneo de lectura
        SELECT @nuevo_id = ISNULL(MAX(ID_viajero), 0) + 1 FROM Viajeros WITH (UPDLOCK, HOLDLOCK);

        INSERT INTO Viajeros (
            ID_viajero,identificacion_viajero,nombre_viajero,apellido_viajero,telefono_viajero,email_viajero,
			fecha_nacimiento_viajero,clave_viajero,ID_direccion)
        VALUES (
            @nuevo_id,NULL,NULL,NULL,@tel_viajero,@email_viajero,NULL,NULL,NULL);
        COMMIT TRANSACTION;
        -- Retornamos el ID
        SELECT @nuevo_id AS id_viajero;

    END TRY
    BEGIN CATCH
        -- Si algo falla, deshacemos cualquier cambio
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrorMessage, 16, 1);
    END CATCH
END
--Prueba: (hay que descomentar la linea)
--exec registrarViajeroTemporal '3795152229', 'carlosdaniel313@gmail.com'
/* Procedimiento para verificar e insertar los datos de la tarjeta con validaciones */
CREATE PROCEDURE verificarDatosTarjetaViajero
	-- 1. AUMENTAMOS LOS TAMAÑOS DE LOS PARÁMETROS 
	-- Para que reciban toda la "basura" completa y podamos atajarla en los IF.
	@num_tarjeta NVARCHAR(50),
	@nombre_titular NVARCHAR(254),
	@vencimiento_tarjeta NVARCHAR(10),
	@cod_seguridad_tarjeta NVARCHAR(10),
	@dni_titular NVARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    -- ==========================================
    -- BLOQUE DE VALIDACIONES
    -- ==========================================
    -- 1. Validar Número de Tarjeta (min 13, max 19 dígitos numéricos)
    IF LEN(@num_tarjeta) < 13 OR LEN(@num_tarjeta) > 19 OR @num_tarjeta LIKE '%[^0-9]%'
    BEGIN
        RAISERROR('El número de tarjeta debe contener entre 13 y 19 dígitos numéricos.', 16, 1);
        RETURN;
    END
    -- 2. Validar DNI (mínimo 8 dígitos numéricos)
    IF LEN(@dni_titular) < 8 OR @dni_titular LIKE '%[^0-9]%'
    BEGIN
        RAISERROR('El DNI debe tener un mínimo de 8 dígitos numéricos.', 16, 1);
        RETURN;
    END
    -- 3. Validar Código de Seguridad (entre 3 y 4 dígitos numéricos)
    IF LEN(@cod_seguridad_tarjeta) < 3 OR LEN(@cod_seguridad_tarjeta) > 4 OR @cod_seguridad_tarjeta LIKE '%[^0-9]%'
    BEGIN
        RAISERROR('El código de seguridad debe tener 3 o 4 dígitos numéricos.', 16, 1);
        RETURN;
    END
    -- 4. Validar Vencimiento (Formato, Mes y Año)
    -- a) Verificamos el formato visual estricto MM/YY y mes válido
    IF @vencimiento_tarjeta NOT LIKE '[0-1][0-9]/[0-9][0-9]' 
       OR CAST(SUBSTRING(@vencimiento_tarjeta, 1, 2) AS INT) NOT BETWEEN 1 AND 12
    BEGIN
        RAISERROR('La fecha de vencimiento no es válida. Utilice el formato MM/YY.', 16, 1);
        RETURN;
    END
    -- b) Verificamos que la tarjeta no esté vencida comparada con hoy
    DECLARE @MesTarjeta INT = CAST(SUBSTRING(@vencimiento_tarjeta, 1, 2) AS INT);
    -- Le sumamos '20' al año para que '25' sea '2025' o '28' sea '2028'
    DECLARE @AnioTarjeta INT = CAST('20' + SUBSTRING(@vencimiento_tarjeta, 4, 2) AS INT);
    -- EOMONTH nos devuelve el último día de ese mes
    DECLARE @FechaVencimiento DATE = EOMONTH(DATEFROMPARTS(@AnioTarjeta, @MesTarjeta, 1));
    -- Comparamos con la fecha actual
    IF @FechaVencimiento < CAST(GETDATE() AS DATE)
    BEGIN
        RAISERROR('La tarjeta ingresada se encuentra vencida.', 16, 1);
        RETURN;
    END
    -- ==========================================
    -- INSERCIÓN Y TRANSACCIÓN
    -- ==========================================
    DECLARE @id_tarjeta INT;
    BEGIN TRY
        BEGIN TRANSACTION;
        SELECT @id_tarjeta = ISNULL(MAX(ID_tarjeta), 0) + 1 FROM Tarjetas WITH (UPDLOCK, HOLDLOCK);
        -- La tabla la inserta normal (Acá las columnas sí respetan sus propios límites físicos)
        INSERT INTO Tarjetas (
            ID_tarjeta, ID_tipo_tarjeta, descripcion, numeros_tarjeta, 
            nombre_titular, dni_titular, vencimiento_tarjeta, cod_seguridad_tarjeta
        )
        VALUES (
            @id_tarjeta, 1, 'Visa', @num_tarjeta, 
            @nombre_titular, @dni_titular, @vencimiento_tarjeta, @cod_seguridad_tarjeta
        );

        COMMIT TRANSACTION;
        SELECT @id_tarjeta AS ID_tarjeta;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrorMessage, 16, 1);
    END CATCH
END
--Prueba: (hay que descomentar la linea)
--exec verificarDatosTarjetaViajero '1231231231231231231','Carlos pineda','12/28','123','95963784'

/*Procedimiento para registrar la reserva del vuelo*/
CREATE PROCEDURE reservarNuevoVuelo
	@fecha_reserva DATETIME,
	@monto_total_vuelo FLOAT,
	@cant_asiento INT,
	@ID_viajero INT,
	@ID_programacion_vuelo INT,
	@ID_clase INT
	AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @id_reserva INT;

    BEGIN TRY
        -- Iniciamos transacción con aislamiento estricto para evitar IDs duplicados en simultáneo
        BEGIN TRANSACTION;

        -- Calculamos el ID asegurando el bloqueo momentáneo de lectura
        SELECT @id_reserva = ISNULL(MAX(ID_reserva_vuelo), 0) + 1 FROM Reservas_Vuelos WITH (UPDLOCK, HOLDLOCK);

        INSERT INTO Reservas_Vuelos(ID_reserva_vuelo,fecha_reserva,monto_total_vuelo,cantidad_asientos,ID_estado_reserva,ID_viajero,ID_programacion_vuelo,ID_clase)
        VALUES (
            @id_reserva,@fecha_reserva,@monto_total_vuelo,@cant_asiento,2,@ID_viajero,@ID_programacion_vuelo,@ID_clase)
        COMMIT TRANSACTION;
        -- Retornamos el ID
        SELECT @id_reserva AS ID_reserva;

    END TRY
    BEGIN CATCH
        -- Si algo falla, deshacemos cualquier cambio
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrorMessage, 16, 1);
    END CATCH
END

/*Procedimiento para actualizar la disponibilidad de los asientos del vuelo (Cuando se realiza la reserva) */
CREATE PROCEDURE actualizarDisponibilidadVuelo
    @id_clase INT,
    @id_programacion_vuelo INT,
    @cant_asientos INT
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @asientosDisponibles INT;

    BEGIN TRY
        BEGIN TRANSACTION;

        -- 1. Verificamos cuántos asientos quedan, bloqueando momentáneamente la fila
        SELECT @asientosDisponibles = asiento_disponible_clase 
        FROM Programaciones_Vuelos_Clases WITH (UPDLOCK, HOLDLOCK)
        WHERE id_programacion_vuelo = @id_programacion_vuelo 
          AND id_clase = @id_clase;

        -- 2. Validamos si hay suficientes lugares para esta compra
        IF @AsientosDisponibles >= @cant_asientos
        BEGIN
            -- Hay lugar: Descontamos los asientos
            UPDATE Programaciones_Vuelos_Clases
            SET asiento_disponible_clase = asiento_disponible_clase - @cant_asientos
            WHERE id_programacion_vuelo = @id_programacion_vuelo 
              AND id_clase = @id_clase;

            COMMIT TRANSACTION;
            PRINT 'Disponibilidad actualizada correctamente.';
        END
        ELSE
        BEGIN
            -- NO hay lugar: Cancelamos la operación y disparamos un error
            ROLLBACK TRANSACTION;
            RAISERROR('No hay suficientes asientos disponibles en esta clase.', 16, 1);
        END

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrorMessage, 16, 1);
    END CATCH
END
/*Caso de prueba: Descuenta dos puestos de clase economica en el vuelo 206
exec actualizarDisponibilidadVuelo 1,206,2
*/
/*Procedimiento para registrar el pago*/
CREATE PROCEDURE registrarPagoReserva
    @fecha_pago DATETIME,
    @monto_total FLOAT,
    @ID_tarjeta INT,
    @ID_reserva_vuelo INT
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @id_pago INT;
    -- Declaramos las variables para el número de transacción
    DECLARE @numero_transaccion INT; 
    DECLARE @EsUnico BIT = 0;
    BEGIN TRY
        -- Iniciamos transacción con aislamiento estricto
        BEGIN TRANSACTION;
        -- 1. Calculamos el ID asegurando el bloqueo momentáneo de lectura
        SELECT @id_pago = ISNULL(MAX(ID_pago), 0) + 1 FROM Pagos WITH (UPDLOCK, HOLDLOCK);
        -- 2. Generamos el Número de Transacción Aleatorio y Único
        WHILE @EsUnico = 0
        BEGIN
            -- Genera un número aleatorio de 8 dígitos (ej: 48192034)
            SET @numero_transaccion = ABS(CHECKSUM(NEWID())) % 90000000 + 10000000;
            -- Verificamos que no exista en la tabla Pagos
            IF NOT EXISTS (SELECT 1 FROM Pagos WHERE numero_transaccion = @numero_transaccion)
            BEGIN
                SET @EsUnico = 1; -- Rompe el bucle porque el número está libre
            END
        END
        -- 3. Insertamos el registro
        INSERT INTO Pagos (ID_pago, fecha_pago, total_pagar, numero_transaccion, ID_tarjeta, ID_reserva_vuelo)
        VALUES (
            @id_pago, @fecha_pago, @monto_total, @numero_transaccion, @ID_tarjeta, @ID_reserva_vuelo
        );
        COMMIT TRANSACTION;
        -- 4. Retornamos tanto el ID como el Nro de Transacción al backend
        SELECT @id_pago AS id_pago
    END TRY
    BEGIN CATCH
        -- Si algo falla, deshacemos cualquier cambio
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrorMessage, 16, 1);
    END CATCH
END
/*Procedimiento para generar el comprobante de la reserva del vuelo*/
CREATE PROCEDURE generarComprobanteReservaVuelo
    @id_pago INT
AS
BEGIN
    SET NOCOUNT ON;

    SELECT 
        -- 1. Datos de la Reserva y Pago
        RV.ID_reserva_vuelo AS id_reserva,
        RV.fecha_reserva,
        RV.monto_total_vuelo AS total_pagar,
        RV.cantidad_asientos,
        ER.descripcion_estado_reserva AS descripcion_estado_reserva,
        P.fecha_pago,
        P.numero_transaccion,

        -- 2. Datos del Viajero
        VJ.email_viajero,

        -- 3. Datos del Vuelo / Itinerario
        AERO.nombre_aerolinea,
        CL.descripcion_clase,
        PV.fecha_salida,
        PV.fecha_llegada,

        -- Origen
        AO.nombre_completo AS aeropuerto_origen,
        PO.nombre_provincia AS provincia_origen,

        -- Destino
        AD.nombre_completo AS aeropuerto_destino,
        PD.nombre_provincia AS provincia_destino,

        -- 4. Datos del Pago (Tarjeta asociada al Pago)
        T.descripcion AS descripcion_tarjeta,
        TT.descripcion_tarjeta AS tipo_tarjeta,
        T.nombre_titular AS titular_tarjeta

    FROM Pagos P
    -- Conectamos el pago con la reserva y la tarjeta
    INNER JOIN Reservas_Vuelos RV ON P.ID_reserva_vuelo = RV.ID_reserva_vuelo
    INNER JOIN Tarjetas T ON P.ID_tarjeta = T.ID_tarjeta
    INNER JOIN Tipos_Tarjetas TT ON T.ID_tipo_tarjeta = TT.ID_tipo_tarjeta
    
    -- El resto de la cadena de Joins desde la reserva
    INNER JOIN Viajeros VJ ON RV.ID_viajero = VJ.ID_viajero
    INNER JOIN Estados_Reserva_Vuelo ER ON RV.ID_estado_reserva = ER.ID_estado_reserva_vuelo
    INNER JOIN Clases CL ON RV.ID_clase = CL.ID_clase
    INNER JOIN Programacion_Vuelos PV ON RV.ID_programacion_vuelo = PV.ID_programacion_vuelo
    
    -- CORRECCIÓN AQUÍ: Se une por ID_vuelo, NO por ID_programacion_vuelo
    INNER JOIN Vuelos V ON PV.ID_vuelo = V.ID_vuelo 
    
    INNER JOIN Aerolineas AERO ON V.ID_aerolinea = AERO.ID_aerolinea

    -- Joins de Ubicación Geográfica (Origen)
    INNER JOIN Aeropuertos AO ON V.origen_ID_aeropuerto = AO.ID_aeropuerto
    INNER JOIN Direcciones DAO ON AO.ID_direccion = DAO.ID_direccion
    INNER JOIN Localidades LO ON DAO.ID_localidad = LO.ID_localidad
    INNER JOIN Provincias PO ON LO.ID_provincia = PO.ID_provincia

    -- Joins de Ubicación Geográfica (Destino)
    INNER JOIN Aeropuertos AD ON V.destino_ID_aeropuerto = AD.ID_aeropuerto
    INNER JOIN Direcciones DAD ON AD.ID_direccion = DAD.ID_direccion
    INNER JOIN Localidades LD ON DAD.ID_localidad = LD.ID_localidad
    INNER JOIN Provincias PD ON LD.ID_provincia = PD.ID_provincia

    WHERE P.ID_pago = @id_pago;
END
/*Caso de prueba:
exec generarComprobanteReservaVuelo 1
*/