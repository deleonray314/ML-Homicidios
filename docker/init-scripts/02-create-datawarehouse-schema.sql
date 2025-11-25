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
-- DIMENSIÓN: dim_departamento
-- Dimensión geográfica de departamentos (DIVIPOLA)
-- ============================================================================
CREATE TABLE IF NOT EXISTS dim_departamento (
    cod_depto INTEGER PRIMARY KEY,
    nom_depto VARCHAR(100) NOT NULL,
    latitud DECIMAL(10, 8),
    longitud DECIMAL(11, 8)
);

CREATE INDEX idx_dim_departamento_nombre ON dim_departamento(nom_depto);

COMMENT ON TABLE dim_departamento IS 'Dimensión de departamentos DIVIPOLA';

-- ============================================================================
-- DIMENSIÓN: dim_municipio
-- Dimensión geográfica de municipios (DIVIPOLA)
-- ============================================================================
CREATE TABLE IF NOT EXISTS dim_municipio (
    cod_mpio INTEGER PRIMARY KEY,
    cod_depto INTEGER NOT NULL REFERENCES dim_departamento(cod_depto),
    nom_mpio VARCHAR(100) NOT NULL,
    tipo VARCHAR(50),
    latitud DECIMAL(10, 8),
    longitud DECIMAL(11, 8)
);

CREATE INDEX idx_dim_municipio_nombre ON dim_municipio(nom_mpio);
CREATE INDEX idx_dim_municipio_depto ON dim_municipio(cod_depto);

COMMENT ON TABLE dim_municipio IS 'Dimensión de municipios DIVIPOLA';

-- ============================================================================
-- DIMENSIÓN: dim_sexo
-- Sexo de las víctimas
-- ============================================================================
CREATE TABLE IF NOT EXISTS dim_sexo (
    sexo_key SERIAL PRIMARY KEY,
    sexo VARCHAR(20) NOT NULL,
    
    -- Constraint único por sexo
    CONSTRAINT uq_sexo UNIQUE (sexo)
);

CREATE INDEX idx_dim_sexo_sexo ON dim_sexo(sexo);

COMMENT ON TABLE dim_sexo IS 'Dimensión de sexo de víctimas';


-- ============================================================================
-- TABLA DE HECHOS: fact_homicidios
-- Eventos de homicidios con referencias a dimensiones
-- ============================================================================
CREATE TABLE IF NOT EXISTS fact_homicidios (
    homicidio_key BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys a dimensiones
    fecha_key INTEGER NOT NULL REFERENCES dim_fecha(fecha_key),
    cod_depto INTEGER NOT NULL REFERENCES dim_departamento(cod_depto),
    cod_mpio INTEGER NOT NULL REFERENCES dim_municipio(cod_mpio),
    sexo_key INTEGER NOT NULL REFERENCES dim_sexo(sexo_key),
    
    -- Atributos del evento
    zona VARCHAR(50),  -- Urbana/Rural/Cabecera/etc
    
    -- Métricas
    cantidad INTEGER NOT NULL DEFAULT 1,
    
    -- Metadatos
    source_id BIGINT,  -- ID del registro en Data Lake
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_fact_cantidad CHECK (cantidad > 0)
);

-- Índices para optimizar queries
CREATE INDEX idx_fact_fecha ON fact_homicidios(fecha_key);
CREATE INDEX idx_fact_depto ON fact_homicidios(cod_depto);
CREATE INDEX idx_fact_mpio ON fact_homicidios(cod_mpio);
CREATE INDEX idx_fact_sexo ON fact_homicidios(sexo_key);
CREATE INDEX idx_fact_zona ON fact_homicidios(zona);
CREATE INDEX idx_fact_loaded_at ON fact_homicidios(loaded_at);

-- Índices compuestos para queries comunes
CREATE INDEX idx_fact_fecha_depto ON fact_homicidios(fecha_key, cod_depto);
CREATE INDEX idx_fact_fecha_mpio ON fact_homicidios(fecha_key, cod_mpio);

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

-- Insertar valores comunes de sexo
INSERT INTO dim_sexo (sexo)
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
    d.cod_depto,
    d.nom_depto,
    COUNT(*) as total_homicidios,
    SUM(h.cantidad) as total_victimas
FROM fact_homicidios h
JOIN dim_departamento d ON h.cod_depto = d.cod_depto
GROUP BY d.cod_depto, d.nom_depto
ORDER BY total_homicidios DESC;

-- Vista: homicidios_por_municipio
CREATE OR REPLACE VIEW v_homicidios_por_municipio AS
SELECT 
    m.cod_mpio,
    m.nom_mpio,
    d.nom_depto,
    COUNT(*) as total_homicidios,
    SUM(h.cantidad) as total_victimas
FROM fact_homicidios h
JOIN dim_municipio m ON h.cod_mpio = m.cod_mpio
JOIN dim_departamento d ON m.cod_depto = d.cod_depto
GROUP BY m.cod_mpio, m.nom_mpio, d.nom_depto
ORDER BY total_homicidios DESC;

-- Vista: homicidios_por_sexo
CREATE OR REPLACE VIEW v_homicidios_por_sexo AS
SELECT 
    s.sexo,
    COUNT(*) as total_homicidios,
    SUM(h.cantidad) as total_victimas
FROM fact_homicidios h
JOIN dim_sexo s ON h.sexo_key = s.sexo_key
GROUP BY s.sexo
ORDER BY total_homicidios DESC;

-- ============================================================================
-- Fin del script de inicialización del Data Warehouse
-- ============================================================================
