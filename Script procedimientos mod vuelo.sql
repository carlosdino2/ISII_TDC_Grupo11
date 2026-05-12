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
	ID_programacion_vuelo, fecha_salida,fecha_llegada,asientos_disponibles, 
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
	AND pv.fecha_salida >= @fecha_salida
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
