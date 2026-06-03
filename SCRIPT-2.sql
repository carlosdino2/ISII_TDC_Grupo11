--Carga de datos de los aeropuestos:
--Agregamos el país
INSERT INTO Paises (ID_pais, nombre_pais)
VALUES (1, 'Argentina');
--Agregamos las provincias
INSERT INTO Provincias (ID_provincia, nombre_provincia, ID_pais)
VALUES 
(1, 'Buenos Aires', 1),
(2, 'Córdoba', 1),
(3, 'Mendoza', 1),
(4, 'Santa Fe', 1),
(5, 'Río Negro', 1),
(6, 'Corrientes',1);
--Agregamos las localidades
INSERT INTO Localidades (ID_localidad, nombre_localidad, ID_provincia)
VALUES
(1, 'Mar del Plata', 1),
(2, 'La Plata', 1),
(3, 'Villa Carlos Paz', 2),
(4, 'Córdoba Capital', 2),
(5, 'Mendoza Capital', 3),
(6, 'San Rafael', 3),
(7, 'Rosario', 4),
(8, 'Santa Fe Capital', 4),
(9, 'Bariloche', 5),
(10, 'El Bolsón', 5),
(11, 'Corrientes', 6);
-- Insertamos direcciones ficticias
INSERT INTO Direcciones (ID_direccion, calle_direccion, numero_direccion, cod_postal, ID_localidad) VALUES
(1, 'Autovía 2 Km 398.5', 1450, '7600', 1),   -- Mar del Plata
(2, 'Av. La Voz del Interior', 8500, '5000', 4), -- Córdoba
(3, 'Ruta Nacional 40 Km 15', 1384, '5539', 5),  -- Mendoza
(4, 'Av. Jorge Newbery', 456, '2000', 7),       -- Rosario
(5, 'Ruta Nacional 11 Km 452', 753, '3000', 8),  -- Santa Fe
(6, 'Ruta Nacional 40 Km 11', 223, '8400', 9),  -- Bariloche
(7, 'Ruta Nacional 12 Km 1030', 1030, '3400', 11); -- Corrientes
--Cargamos los aeropuertos
INSERT INTO Aeropuertos (ID_aeropuerto, nombre_completo, ID_direccion) VALUES
(1, 'Aeropuerto Internacional Ástor Piazzolla', 1),   -- Mar del Plata
(2, 'Aeropuerto Internacional Ing. Ambrosio Taravella', 2), -- Córdoba
(3, 'Aeropuerto Internacional El Plumerillo', 3),   -- Mendoza
(4, 'Aeropuerto Internacional Rosario Islas Malvinas', 4), -- Rosario
(5, 'Aeropuerto de Sauce Viejo', 5),                -- Santa Fe
(6, 'Aeropuerto Internacional Teniente Luis Candelaria', 6) -- Bariloche
(7, 'Aeropuerto Internacional Dr. Fernando Piragine Niveyro', 7); -- Corrientes
-- Carga de Aerolíneas
INSERT INTO Aerolineas (ID_aerolinea, nombre_aerolinea) VALUES 
(1, 'Aerolíneas Argentinas'),
(2, 'Flybondi'),
(3, 'JetSmart');

-- Carga de Clases
INSERT INTO Clases (ID_clase, descripcion_clase) VALUES 
(1, 'Económica'), -- El precio real lo ponemos en la programación
(2, 'Ejecutiva'),
(3, 'Primera Clase');

-- Carga de Estados de Vuelo
INSERT INTO Estados_Vuelos (ID_estado_vuelo, descripcion_estado_vuelo) VALUES 
(1, 'Programado'),
(2, 'A tiempo'),
(3, 'Demorado'),
(4, 'Cancelado');
-- Vuelos 
INSERT INTO Vuelos (ID_vuelo, numero_vuelo, duracion_estimada, origen_ID_aeropuerto, destino_ID_aeropuerto, ID_aerolinea) VALUES
(1, 1500, 45, 7, 4, 1), -- Corrientes -> Rosario
(2, 1501, 45, 4, 7, 1), -- Rosario -> Corrientes
(3, 2020, 60, 2, 3, 2), -- Córdoba -> Mendoza
(4, 3015, 110, 3, 6, 3), -- Mendoza -> Bariloche
(5, 4050, 95, 6, 2, 2), -- Bariloche -> Córdoba
(6, 1605, 125, 7, 6, 1), -- Corrientes -> Bariloche
(7, 1610, 160, 7, 6, 2); -- Corrientes -> Bariloche

-- Programaciones para el 22 de Octubre de 2024
INSERT INTO Programacion_Vuelos (ID_programacion_vuelo, fecha_salida, fecha_llegada, asientos_disponibles, ID_vuelo, ID_estado_vuelo) VALUES
(201, '2026-10-22 08:30:00', '2026-10-22 10:05:00', 120, 1, 1), -- Ctes -> Ros (Mañana)
(202, '2026-10-22 16:00:00', '2026-10-22 17:35:00', 120, 2, 1), -- Ros -> Ctes (Tarde)
(203, '2026-10-22 11:00:00', '2026-10-22 12:05:00', 189, 3, 2), -- Cba -> Mza (A tiempo)
(204, '2026-10-22 14:00:00', '2026-10-22 15:55:00', 150, 4, 1), -- Mza -> Brc
(205, '2026-10-22 20:00:00', '2026-10-22 21:40:00', 189, 5, 1), -- Brc -> Cba (Noche)
(206, '2026-10-22 21:00:00', '2026-10-22 23:05:00', 150, 6, 1), -- Ctes -> Brc
(207, '2026-10-22 20:00:00', '2026-10-22 22:00:00', 150, 7, 1); -- Ctes -> Brc

-- Insertamos los precios y asientos disponibles por clase para estos vuelos específicos
--Salida 22/10/2026 Llegada: 22/10/2026
-- Vuelo 201: Corrientes a Rosarío
INSERT INTO Programaciones_Vuelos_Clases (ID_clase, ID_programacion_vuelo, asiento_disponible_clase, precio_clase) VALUES
(1, 201, 100, 35500.00), -- Económica
(2, 201, 20, 78000.00);  -- Ejecutiva

-- Vuelo 202: Rosarío a Corrientes (Regreso)
INSERT INTO Programaciones_Vuelos_Clases (ID_clase, ID_programacion_vuelo, asiento_disponible_clase, precio_clase) VALUES
(1, 202, 100, 32000.00), -- Económica
(2, 202, 20, 75000.00); -- Ejecutiva

-- Vuelo 203: Córdoba a Mendoza
INSERT INTO Programaciones_Vuelos_Clases (ID_clase, ID_programacion_vuelo, asiento_disponible_clase, precio_clase) VALUES
(1, 203, 189, 28000.00); -- Economica

-- Vuelo 204: Mendoza a Bariloche
INSERT INTO Programaciones_Vuelos_Clases (ID_clase, ID_programacion_vuelo, asiento_disponible_clase, precio_clase) VALUES
(1, 204, 130, 42000.00), -- Económica
(2, 204, 20, 95000.00); -- Ejecutiva

-- Vuelo 205: Bariloche a Córdoba
INSERT INTO Programaciones_Vuelos_Clases (ID_clase, ID_programacion_vuelo, asiento_disponible_clase, precio_clase) VALUES
(1, 205, 189, 39500.00); -- Económica

-- Detalle de las 3 clases para el vuelo 206
--Vuelo 2026: Corrientes a Bariloche
--Aerolineas Argentinas
INSERT INTO Programaciones_Vuelos_Clases (ID_clase, ID_programacion_vuelo, asiento_disponible_clase, precio_clase) VALUES
(1, 206, 120, 45000.00),  -- Económica
(2, 206, 22, 95000.00),   -- Ejecutiva
(3, 206, 8, 145000.00);   -- Primera Clase
--Flybondi
INSERT INTO Programaciones_Vuelos_Clases (ID_clase, ID_programacion_vuelo, asiento_disponible_clase, precio_clase) VALUES
(1, 207, 120, 90000.00)  -- Económica
