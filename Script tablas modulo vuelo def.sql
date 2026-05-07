-- use database viajefacil1
GO

-- 1. TABLAS MAESTRAS (Sin dependencias)
CREATE TABLE Aerolineas(
    ID_aerolinea INT NOT NULL,
    nombre_aerolinea VARCHAR(100) NOT NULL,
    CONSTRAINT PK_Aerolineas PRIMARY KEY (ID_aerolinea)
);

CREATE TABLE Clases(
    ID_clase INT NOT NULL,
    descripcion_clase VARCHAR(100) NOT NULL, 
    CONSTRAINT PK_Clases PRIMARY KEY (ID_clase)
);

CREATE TABLE Estados_Vuelos(
    ID_estado_vuelo INT NOT NULL,
    descripcion_estado_vuelo VARCHAR(100) NOT NULL,
    CONSTRAINT PK_Estados_Vuelos PRIMARY KEY (ID_estado_vuelo)
);

CREATE TABLE Estados_Reserva_Vuelo(
    ID_estado_reserva_vuelo INT NOT NULL,
    descripcion_estado_reserva VARCHAR(100) NOT NULL,
    CONSTRAINT PK_Estados_Reserva PRIMARY KEY (ID_estado_reserva_vuelo)
);

CREATE TABLE Tipos_Tarjetas(
    ID_tipo_tarjeta INT NOT NULL,
    descripcion_tarjeta VARCHAR(100) NOT NULL,
    CONSTRAINT PK_Tipos_Tarjetas PRIMARY KEY (ID_tipo_tarjeta)
);

-- 2. INFRAESTRUCTURA Y USUARIOS
CREATE TABLE Aeropuertos(
    ID_aeropuerto INT NOT NULL,
    nombre_completo VARCHAR(300) NOT NULL,
    ID_direccion INT NOT NULL,
    CONSTRAINT PK_Aeropuertos PRIMARY KEY (ID_aeropuerto),
    CONSTRAINT FK_Aeropuertos_Direcciones FOREIGN KEY (ID_direccion) REFERENCES Direcciones(ID_direccion)
);

CREATE TABLE Tarjetas(
    ID_tarjeta INT NOT NULL,
    ID_tipo_tarjeta INT NOT NULL,
    descripcion VARCHAR(100) NOT NULL,
    numeros_tarjeta VARCHAR(19) NOT NULL,
    nombre_titular VARCHAR(100) NOT NULL,
    apellido_titular VARCHAR(100) NOT NULL,
    dni_titular VARCHAR(8) NOT NULL,
    vencimiento_tarjeta CHAR(5) NOT NULL, -- Formato MM/YY

    PrimerDiaDelMesVencimiento AS (
        DATEFROMPARTS(
            2000 + TRY_CAST(SUBSTRING(vencimiento_tarjeta, 4, 2) AS INT), 
            TRY_CAST(SUBSTRING(vencimiento_tarjeta, 1, 2) AS INT),        
            1                                                            
        )
    ) PERSISTED,

    -- Calculamos el último día usando EOMONTH
    UltimoDiaDelMesVencimiento AS (
        EOMONTH(
            DATEFROMPARTS(
                2000 + TRY_CAST(SUBSTRING(vencimiento_tarjeta, 4, 2) AS INT),
                TRY_CAST(SUBSTRING(vencimiento_tarjeta, 1, 2) AS INT),
                1
            )
        )
    ) PERSISTED,

    CONSTRAINT PK_Tarjetas PRIMARY KEY (ID_tarjeta),
    CONSTRAINT FK_Tarjetas_Tipo FOREIGN KEY (ID_tipo_tarjeta) REFERENCES Tipos_Tarjetas(ID_tipo_tarjeta),
    -- Validaciones de formato
    CONSTRAINT CK_Tarjetas_Barra CHECK (SUBSTRING(vencimiento_tarjeta, 3, 1) = '/'),
    CONSTRAINT CK_Tarjetas_Mes CHECK (TRY_CAST(SUBSTRING(vencimiento_tarjeta, 1, 2) AS INT) BETWEEN 1 AND 12),
    CONSTRAINT CK_DNI_Longitud CHECK (LEN(dni_titular) BETWEEN 7 AND 8),
    CONSTRAINT CK_Tarjeta_Longitud CHECK (LEN(numeros_tarjeta) BETWEEN 13 AND 19)
);

-- 3. LÓGICA DE VUELOS
CREATE TABLE Vuelos(
    ID_vuelo INT NOT NULL,
    numero_vuelo INT NOT NULL,
    duracion_estimada INT NOT NULL,
    origen_ID_aeropuerto INT NOT NULL,
    destino_ID_aeropuerto INT NOT NULL,
    ID_aerolinea INT NOT NULL,

    CONSTRAINT PK_Vuelos PRIMARY KEY (ID_vuelo),
    CONSTRAINT CK_Vuelo_Duracion_Positiva CHECK (duracion_estimada >= 0),
    CONSTRAINT FK_Vuelos_AeropuertoOrigen FOREIGN KEY (origen_ID_aeropuerto) REFERENCES Aeropuertos (ID_aeropuerto),
    CONSTRAINT FK_Vuelos_AeropuertoDestino FOREIGN KEY (destino_ID_aeropuerto) REFERENCES Aeropuertos (ID_aeropuerto),
    CONSTRAINT FK_Vuelos_Aerolineas FOREIGN KEY (ID_aerolinea) REFERENCES Aerolineas (ID_aerolinea)
);

CREATE TABLE Programacion_Vuelos(
    ID_programacion_vuelo INT NOT NULL,
    fecha_salida DATETIME2 NOT NULL,
    fecha_llegada DATETIME2 NOT NULL,
    asientos_disponibles INT NOT NULL,
    ID_vuelo INT NOT NULL,
    ID_estado_vuelo INT NOT NULL,

    CONSTRAINT PK_Programacion PRIMARY KEY (ID_programacion_vuelo),
    CONSTRAINT CK_Asientos_Positivos CHECK (asientos_disponibles >= 0),
    CONSTRAINT CK_Fecha_Logica CHECK (fecha_llegada > fecha_salida),
    CONSTRAINT FK_ProgVuelos_Vuelos FOREIGN KEY (ID_vuelo) REFERENCES Vuelos (ID_vuelo),
    CONSTRAINT FK_ProgVuelos_Estados FOREIGN KEY (ID_estado_vuelo) REFERENCES Estados_Vuelos (ID_estado_vuelo)
);

CREATE TABLE Programaciones_Vuelos_Clases(
    ID_clase INT NOT NULL,
    ID_programacion_vuelo INT NOT NULL,
    asiento_disponible_clase INT NOT NULL,
	precio_clase DECIMAL(18, 2) NOT NULL,
    CONSTRAINT PK_Prog_Vuelos_Clases PRIMARY KEY (ID_clase, ID_programacion_vuelo),
    CONSTRAINT CK_Precio_Clase_Positivos CHECK (precio_clase >= 0.00),
    CONSTRAINT FK_PVC_Clase FOREIGN KEY (ID_clase) REFERENCES Clases (ID_clase),
    CONSTRAINT FK_PVC_Prog FOREIGN KEY (ID_programacion_vuelo) REFERENCES Programacion_Vuelos (ID_programacion_vuelo),
    CONSTRAINT CK_Asiento_Clase_Positivo CHECK (asiento_disponible_clase >= 0)
);

-- 4. TRANSACCIONES
CREATE TABLE Reservas_Vuelos(
    ID_reserva_vuelo INT NOT NULL,
    fecha_reserva DATETIME2 NOT NULL,
    monto_total_vuelo DECIMAL (18, 2) NOT NULL,
    cantidad_asientos INT NOT NULL,
    ID_estado_reserva INT NOT NULL,
    ID_viajero INT NOT NULL,
    ID_programacion_vuelo INT NOT NULL,
    ID_clase INT NOT NULL,

    CONSTRAINT PK_Reservas_Vuelos PRIMARY KEY (ID_reserva_vuelo),
    CONSTRAINT FK_Reservas_Estados FOREIGN KEY (ID_estado_reserva) REFERENCES Estados_Reserva_Vuelo (ID_estado_reserva_vuelo),
    CONSTRAINT FK_Reservas_Viajero FOREIGN KEY (ID_viajero) REFERENCES Viajeros (ID_viajero),
    CONSTRAINT FK_Reservas_ProgVuelo FOREIGN KEY (ID_programacion_vuelo) REFERENCES Programacion_Vuelos (ID_programacion_vuelo),
    CONSTRAINT FK_Reservas_Clase FOREIGN KEY (ID_clase) REFERENCES Clases (ID_clase),
    CONSTRAINT CK_Asiento_Reserva_Positivo CHECK (cantidad_asientos > 0)
);

CREATE TABLE Pagos(
    ID_pago INT NOT NULL,
    fecha_pago DATETIME2 NOT NULL,
    total_pagar DECIMAL(18, 2) NOT NULL,
    numero_transaccion FLOAT NOT NULL,
    ID_tarjeta INT NOT NULL,
    ID_reserva_vuelo INT NOT NULL,

    CONSTRAINT PK_Pagos PRIMARY KEY (ID_pago),
    CONSTRAINT UQ_Pagos_Transaccion UNIQUE (numero_transaccion),
    CONSTRAINT FK_Pagos_Tarjeta FOREIGN KEY (ID_tarjeta) REFERENCES Tarjetas (ID_tarjeta),
    CONSTRAINT FK_Pagos_Reserva FOREIGN KEY (ID_reserva_vuelo) REFERENCES Reservas_Vuelos(ID_reserva_vuelo)
);

CREATE TABLE Facturas(
    ID_factura INT NOT NULL,
    fecha_factura DATETIME2 NOT NULL,
    detalle VARCHAR(500) NOT NULL,
    monto_total DECIMAL(18, 2) NOT NULL,
    ID_pago INT NOT NULL,

    CONSTRAINT PK_Facturas PRIMARY KEY (ID_factura),
    CONSTRAINT FK_Facturas_Pagos FOREIGN KEY (ID_pago) REFERENCES Pagos(ID_pago)
);