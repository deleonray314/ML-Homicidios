-- ============================================================================
-- Data Warehouse - Esquema de Base de Datos (Modelo Estrella)
-- ============================================================================
-- Propósito: Almacenar datos procesados en modelo estrella para análisis y ML
-- Basado en: docs/star_schema.md
-- ============================================================================

-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- DIMENSIÓN: dim_fecha
-- Dimensión temporal con granularidad diaria
-- ============================================================================
CREATE TABLE IF NOT EXISTS dim_fecha (
    fecha_key SERIAL PRIMARY KEY,
    fecha DATE UNIQUE NOT NULL,
    
    -- Componentes de fecha
    año SMALLINT NOT NULL,
    mes SMALLINT NOT NULL,
    dia SMALLINT NOT NULL,
    trimestre SMALLINT NOT NULL,
    semana_año SMALLINT NOT NULL,
    dia_semana SMALLINT NOT NULL,
    
    -- Nombres descriptivos
    nombre_mes VARCHAR(20) NOT NULL,
    nombre_dia_semana VARCHAR(20) NOT NULL,
    
    -- Flags
    es_fin_semana BOOLEAN NOT NULL,
    es_festivo BOOLEAN DEFAULT FALSE,
    
    CONSTRAINT chk_mes CHECK (mes BETWEEN 1 AND 12),
    CONSTRAINT chk_dia CHECK (dia BETWEEN 1 AND 31),
    CONSTRAINT chk_trimestre CHECK (trimestre BETWEEN 1 AND 4),
    CONSTRAINT chk_dia_semana CHECK (dia_semana BETWEEN 1 AND 7)
);

CREATE INDEX idx_dim_fecha_fecha ON dim_fecha(fecha);
CREATE INDEX idx_dim_fecha_año_mes ON dim_fecha(año, mes);

COMMENT ON TABLE dim_fecha IS 'Dimensión temporal para análisis de series de tiempo';

-- ============================================================================
-- DIMENSIÓN: dim_ubicacion
-- Dimensión geográfica enriquecida con DIVIPOLA
-- ============================================================================
CREATE TABLE IF NOT EXISTS dim_ubicacion (
    ubicacion_key SERIAL PRIMARY KEY,
    
    -- Departamento
    cod_depto VARCHAR(2) NOT NULL,
    nom_depto VARCHAR(100) NOT NULL,
    depto_latitud DECIMAL(10, 8),
    depto_longitud DECIMAL(11, 8),
    
    -- Municipio
    cod_muni VARCHAR(5) NOT NULL,
    nom_muni VARCHAR(100) NOT NULL,
    tipo_municipio VARCHAR(50),  -- Urbano/Rural
    muni_latitud DECIMAL(10, 8),
    muni_longitud DECIMAL(11, 8),
    
    -- Zona del hecho
    zona VARCHAR(50),  -- Urbana/Rural/Cabecera/etc
    
    -- Constraint único por combinación
    CONSTRAINT uq_ubicacion UNIQUE (cod_depto, cod_muni, zona)
);

CREATE INDEX idx_dim_ubicacion_depto ON dim_ubicacion(cod_depto);
CREATE INDEX idx_dim_ubicacion_muni ON dim_ubicacion(cod_muni);

COMMENT ON TABLE dim_ubicacion IS 'Dimensión geográfica enriquecida con DIVIPOLA';

-- ============================================================================
-- DIMENSIÓN: dim_victima
-- Características demográficas de las víctimas
-- ============================================================================
CREATE TABLE IF NOT EXISTS dim_victima (
    victima_key SERIAL PRIMARY KEY,
    sexo VARCHAR(20) NOT NULL,
    
    -- Constraint único por sexo
    CONSTRAINT uq_victima UNIQUE (sexo)
);

CREATE INDEX idx_dim_victima_sexo ON dim_victima(sexo);

COMMENT ON TABLE dim_victima IS 'Dimensión demográfica de víctimas';

-- ============================================================================
-- DIMENSIÓN: dim_arma
-- Tipos de armas utilizadas (preparado para expansión futura)
-- ============================================================================
CREATE TABLE IF NOT EXISTS dim_arma (
    arma_key SERIAL PRIMARY KEY,
    tipo_arma VARCHAR(100) NOT NULL,
    categoria_arma VARCHAR(50),  -- Fuego, Blanca, Contundente, etc.
    
    CONSTRAINT uq_arma UNIQUE (tipo_arma)
);

CREATE INDEX idx_dim_arma_tipo ON dim_arma(tipo_arma);

COMMENT ON TABLE dim_arma IS 'Dimensión de tipos de armas (expansión futura)';

-- ============================================================================
-- TABLA DE HECHOS: fact_homicidios
-- Eventos de homicidios con referencias a dimensiones
-- ============================================================================
CREATE TABLE IF NOT EXISTS fact_homicidios (
    homicidio_key BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys a dimensiones
    fecha_key INTEGER NOT NULL REFERENCES dim_fecha(fecha_key),
    ubicacion_key INTEGER NOT NULL REFERENCES dim_ubicacion(ubicacion_key),
    victima_key INTEGER NOT NULL REFERENCES dim_victima(victima_key),
    arma_key INTEGER REFERENCES dim_arma(arma_key),  -- Nullable por ahora
    
    -- Métricas
    cantidad INTEGER NOT NULL DEFAULT 1,
    
    -- Metadatos
    source_id BIGINT,  -- ID del registro en Data Lake
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_fact_cantidad CHECK (cantidad > 0)
);

-- Índices para optimizar queries
CREATE INDEX idx_fact_fecha ON fact_homicidios(fecha_key);
CREATE INDEX idx_fact_ubicacion ON fact_homicidios(ubicacion_key);
CREATE INDEX idx_fact_victima ON fact_homicidios(victima_key);
CREATE INDEX idx_fact_arma ON fact_homicidios(arma_key);
CREATE INDEX idx_fact_loaded_at ON fact_homicidios(loaded_at);

-- Índice compuesto para queries comunes
CREATE INDEX idx_fact_fecha_ubicacion ON fact_homicidios(fecha_key, ubicacion_key);

COMMENT ON TABLE fact_homicidios IS 'Tabla de hechos con eventos de homicidios';

-- ============================================================================
-- Tabla: etl_log
-- Log de procesos ETL (auditoría)
-- ============================================================================
CREATE TABLE IF NOT EXISTS etl_log (
    id BIGSERIAL PRIMARY KEY,
    process_name VARCHAR(100) NOT NULL,
    records_processed INTEGER NOT NULL,
    records_inserted INTEGER NOT NULL,
    records_updated INTEGER NOT NULL,
    records_failed INTEGER DEFAULT 0,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    
    CONSTRAINT chk_etl_status CHECK (status IN ('success', 'failed', 'partial'))
);

CREATE INDEX idx_etl_log_process ON etl_log(process_name, completed_at DESC);

COMMENT ON TABLE etl_log IS 'Log de auditoría de procesos ETL';

-- ============================================================================
-- Datos iniciales / Seeds
-- ============================================================================

-- Insertar valor por defecto para arma (cuando no se especifica)
INSERT INTO dim_arma (tipo_arma, categoria_arma)
VALUES ('NO ESPECIFICADO', 'DESCONOCIDO')
ON CONFLICT (tipo_arma) DO NOTHING;

-- Insertar valores comunes de sexo
INSERT INTO dim_victima (sexo)
VALUES 
    ('HOMBRE'),
    ('MUJER'),
    ('NO REPORTA')
ON CONFLICT (sexo) DO NOTHING;

-- Insertar registro inicial en log
INSERT INTO etl_log (process_name, records_processed, records_inserted, records_updated, started_at, status)
VALUES ('system_init', 0, 0, 0, CURRENT_TIMESTAMP, 'success')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Vistas útiles para análisis
-- ============================================================================

-- Vista: homicidios_por_mes
CREATE OR REPLACE VIEW v_homicidios_por_mes AS
SELECT 
    f.año,
    f.mes,
    f.nombre_mes,
    COUNT(*) as total_homicidios,
    SUM(h.cantidad) as total_victimas
FROM fact_homicidios h
JOIN dim_fecha f ON h.fecha_key = f.fecha_key
GROUP BY f.año, f.mes, f.nombre_mes
ORDER BY f.año, f.mes;

-- Vista: homicidios_por_departamento
CREATE OR REPLACE VIEW v_homicidios_por_departamento AS
SELECT 
    u.cod_depto,
    u.nom_depto,
    COUNT(*) as total_homicidios,
    SUM(h.cantidad) as total_victimas
FROM fact_homicidios h
JOIN dim_ubicacion u ON h.ubicacion_key = u.ubicacion_key
GROUP BY u.cod_depto, u.nom_depto
ORDER BY total_homicidios DESC;

-- Vista: homicidios_por_sexo
CREATE OR REPLACE VIEW v_homicidios_por_sexo AS
SELECT 
    v.sexo,
    COUNT(*) as total_homicidios,
    SUM(h.cantidad) as total_victimas
FROM fact_homicidios h
JOIN dim_victima v ON h.victima_key = v.victima_key
GROUP BY v.sexo
ORDER BY total_homicidios DESC;

-- ============================================================================
-- Fin del script de inicialización del Data Warehouse
-- ============================================================================
