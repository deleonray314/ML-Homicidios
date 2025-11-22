-- ============================================================================
-- Data Lake - Esquema de Base de Datos
-- ============================================================================
-- Propósito: Almacenar datos crudos con transformaciones mínimas
-- Nombres de columnas: EXACTOS de la API de Datos Abiertos
-- ============================================================================

-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Tabla: raw_homicidios
-- Datos crudos de homicidios desde la API
-- ============================================================================
CREATE TABLE IF NOT EXISTS raw_homicidios (
    -- ID único generado internamente
    id BIGSERIAL PRIMARY KEY,
    
    -- Campos EXACTOS de la API
    fecha_hecho DATE,
    cod_depto VARCHAR(2),
    departamento VARCHAR(100),
    cod_muni VARCHAR(5),
    municipio VARCHAR(100),
    zona VARCHAR(50),
    sexo VARCHAR(20),
    cantidad INTEGER,
    
    -- Metadatos de carga
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_api VARCHAR(100) DEFAULT 'datos.gov.co',
    
    -- Índices para búsquedas rápidas
    CONSTRAINT chk_cantidad_positive CHECK (cantidad >= 0)
);

-- Índices para optimizar consultas
CREATE INDEX idx_raw_homicidios_fecha ON raw_homicidios(fecha_hecho);
CREATE INDEX idx_raw_homicidios_depto ON raw_homicidios(cod_depto);
CREATE INDEX idx_raw_homicidios_muni ON raw_homicidios(cod_muni);
CREATE INDEX idx_raw_homicidios_loaded_at ON raw_homicidios(loaded_at);

-- ============================================================================
-- Tabla: raw_divipola_departamentos
-- Datos de DIVIPOLA Departamentos (carga única)
-- ============================================================================
CREATE TABLE IF NOT EXISTS raw_divipola_departamentos (
    -- ID único generado internamente
    id SERIAL PRIMARY KEY,
    
    -- Campos EXACTOS de la API
    cod_dpto VARCHAR(2) UNIQUE NOT NULL,
    nom_dpto VARCHAR(100) NOT NULL,
    latitud DECIMAL(10, 8),
    longitud DECIMAL(11, 8),
    geo_departamento TEXT,  -- Geometría en formato JSON/GeoJSON
    
    -- Metadatos de carga
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_api VARCHAR(100) DEFAULT 'datos.gov.co'
);

-- Índice único en código de departamento
CREATE UNIQUE INDEX idx_divipola_depto_cod ON raw_divipola_departamentos(cod_dpto);

-- ============================================================================
-- Tabla: raw_divipola_municipios
-- Datos de DIVIPOLA Municipios (carga única)
-- ============================================================================
CREATE TABLE IF NOT EXISTS raw_divipola_municipios (
    -- ID único generado internamente
    id SERIAL PRIMARY KEY,
    
    -- Campos EXACTOS de la API
    cod_dpto VARCHAR(2) NOT NULL,
    nom_dpto VARCHAR(100),
    cod_mpio VARCHAR(5) UNIQUE NOT NULL,
    nom_mpio VARCHAR(100) NOT NULL,
    tipo VARCHAR(50),  -- Urbano/Rural
    latitud DECIMAL(10, 8),
    longitud DECIMAL(11, 8),
    geo_municipio TEXT,  -- Geometría en formato JSON/GeoJSON
    
    -- Metadatos de carga
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_api VARCHAR(100) DEFAULT 'datos.gov.co'
);

-- Índices para optimizar joins
CREATE UNIQUE INDEX idx_divipola_muni_cod ON raw_divipola_municipios(cod_mpio);
CREATE INDEX idx_divipola_muni_depto ON raw_divipola_municipios(cod_dpto);

-- ============================================================================
-- Tabla: data_load_log
-- Log de cargas de datos (auditoría)
-- ============================================================================
CREATE TABLE IF NOT EXISTS data_load_log (
    id BIGSERIAL PRIMARY KEY,
    dataset_name VARCHAR(100) NOT NULL,  -- 'homicidios', 'departamentos', 'municipios'
    load_type VARCHAR(20) NOT NULL,      -- 'initial', 'incremental'
    records_loaded INTEGER NOT NULL,
    load_started_at TIMESTAMP NOT NULL,
    load_completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'success', -- 'success', 'failed', 'partial'
    error_message TEXT,
    
    CONSTRAINT chk_load_type CHECK (load_type IN ('initial', 'incremental')),
    CONSTRAINT chk_status CHECK (status IN ('success', 'failed', 'partial'))
);

-- Índice para consultas de auditoría
CREATE INDEX idx_load_log_dataset ON data_load_log(dataset_name, load_completed_at DESC);

-- ============================================================================
-- Comentarios en tablas (documentación)
-- ============================================================================
COMMENT ON TABLE raw_homicidios IS 'Datos crudos de homicidios desde API de Datos Abiertos';
COMMENT ON TABLE raw_divipola_departamentos IS 'Catálogo de departamentos DIVIPOLA (DANE)';
COMMENT ON TABLE raw_divipola_municipios IS 'Catálogo de municipios DIVIPOLA (DANE)';
COMMENT ON TABLE data_load_log IS 'Log de auditoría de cargas de datos';

-- ============================================================================
-- Grants (permisos)
-- ============================================================================
-- El usuario de la aplicación tendrá permisos completos en estas tablas
-- (se configurará desde la aplicación Python)

-- ============================================================================
-- Datos iniciales / Seeds (opcional)
-- ============================================================================
-- Insertar registro inicial en log
INSERT INTO data_load_log (dataset_name, load_type, records_loaded, load_started_at, status)
VALUES ('system', 'initial', 0, CURRENT_TIMESTAMP, 'success')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Fin del script de inicialización del Data Lake
-- ============================================================================
