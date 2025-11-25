-- ============================================================================
-- Data Lake - Esquema de Base de Datos
-- ============================================================================
-- Propósito: Almacenar datos crudos con transformaciones mínimas
-- Nombres de columnas: EXACTOS de la API de Datos Abiertos
-- Códigos como INTEGER para permitir foreign keys
-- ============================================================================

-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Tabla: raw_homicidios
-- Datos crudos de homicidios desde la API
-- ============================================================================
CREATE TABLE IF NOT EXISTS raw_homicidios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fecha_hecho DATE,
    cod_depto INTEGER,
    departamento VARCHAR(100),
    cod_muni INTEGER,
    municipio VARCHAR(100),
    zona VARCHAR(50),
    sexo VARCHAR(20),
    cantidad INTEGER DEFAULT 1,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_api VARCHAR(100) DEFAULT 'datos_abiertos_api'
);

COMMENT ON TABLE raw_homicidios IS 'Datos crudos de homicidios desde API Datos Abiertos';

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
    cod_dpto INTEGER PRIMARY KEY,
    nom_dpto VARCHAR(100),
    latitud DECIMAL(10, 8),
    longitud DECIMAL(11, 8),
    geo_departamento TEXT,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_api VARCHAR(100) DEFAULT 'datos_abiertos_api'
);

COMMENT ON TABLE raw_divipola_departamentos IS 'Catálogo de departamentos DIVIPOLA';

-- ============================================================================
-- Tabla: raw_divipola_municipios
-- Datos de DIVIPOLA Municipios (carga única)
-- ============================================================================
CREATE TABLE IF NOT EXISTS raw_divipola_municipios (
    cod_dpto INTEGER,
    nom_dpto VARCHAR(100),
    cod_mpio INTEGER PRIMARY KEY,
    nom_mpio VARCHAR(100),
    tipo VARCHAR(50),
    latitud DECIMAL(10, 8),
    longitud DECIMAL(11, 8),
    geo_municipio TEXT,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_api VARCHAR(100) DEFAULT 'datos_abiertos_api'
);

COMMENT ON TABLE raw_divipola_municipios IS 'Catálogo de municipios DIVIPOLA';

-- Índice para optimizar joins
CREATE INDEX idx_divipola_muni_depto ON raw_divipola_municipios(cod_dpto);

-- ============================================================================
-- Tabla: data_load_log
-- Log de cargas de datos (auditoría)
-- ============================================================================
CREATE TABLE IF NOT EXISTS data_load_log (
    id BIGSERIAL PRIMARY KEY,
    dataset_name VARCHAR(100) NOT NULL,
    load_type VARCHAR(20) NOT NULL,
    records_loaded INTEGER NOT NULL,
    load_started_at TIMESTAMP NOT NULL,
    load_completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT
);

COMMENT ON TABLE data_load_log IS 'Log de auditoría de cargas de datos';

-- Índice para consultas de auditoría
CREATE INDEX idx_load_log_dataset ON data_load_log(dataset_name, load_completed_at DESC);

-- ============================================================================
-- Datos iniciales / Seeds
-- ============================================================================
INSERT INTO data_load_log (dataset_name, load_type, records_loaded, load_started_at, status)
VALUES ('system', 'initial', 0, CURRENT_TIMESTAMP, 'success')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Fin del script de inicialización del Data Lake
-- ============================================================================
