"""
Cargador de datos al Data Lake (PostgreSQL).

Maneja la carga inicial y incremental de datos desde la API de Datos Abiertos
a las tablas raw_* del Data Lake.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values

from src.config.settings import settings
from src.data_ingestion.api_client import DatosAbiertosClient
from src.data_ingestion.db_connection import DatabaseConnection
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataLakeLoader:
    """Cargador de datos al Data Lake."""
    
    def __init__(
        self,
        db: Optional[DatabaseConnection] = None,
        api_client: Optional[DatosAbiertosClient] = None
    ):
        """
        Inicializar cargador.
        
        Args:
            db: Conexión a base de datos (crea una nueva si es None)
            api_client: Cliente de API (crea uno nuevo si es None)
        """
        self.db = db or DatabaseConnection()
        self.api_client = api_client or DatosAbiertosClient()
        
        logger.info("DataLakeLoader inicializado")
    
    def _log_data_load(
        self,
        dataset_name: str,
        load_type: str,
        records_loaded: int,
        started_at: datetime,
        status: str = "success",
        error_message: Optional[str] = None
    ):
        """
        Registrar carga en la tabla de auditoría.
        
        Args:
            dataset_name: Nombre del dataset
            load_type: Tipo de carga ('initial', 'incremental', 'full')
            records_loaded: Número de registros cargados
            started_at: Timestamp de inicio
            status: Estado ('success', 'failed', 'partial')
            error_message: Mensaje de error si aplica
        """
        query = """
            INSERT INTO data_load_log (
                dataset_name, load_type, records_loaded,
                load_started_at, load_completed_at, status, error_message
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            dataset_name,
            load_type,
            records_loaded,
            started_at,
            datetime.now(),
            status,
            error_message
        )
        
        try:
            self.db.execute_query(query, params)
            logger.info(f"Log de carga registrado: {dataset_name} - {records_loaded} registros")
        except Exception as e:
            logger.error(f"Error registrando log de carga: {e}")
    
    def load_homicidios_initial(self, batch_size: int = 1000) -> int:
        """
        Carga inicial completa de homicidios.
        
        Args:
            batch_size: Tamaño de lote para inserts
        
        Returns:
            Número de registros cargados
        """
        started_at = datetime.now()
        dataset_name = "raw_homicidios"
        
        logger.info("🚀 Iniciando carga inicial de homicidios")
        
        try:
            # Extraer todos los datos de la API
            logger.info("Extrayendo datos de API...")
            records = self.api_client.fetch_homicidios_paginated(
                page_size=batch_size
            )
            
            if not records:
                logger.warning("No se encontraron registros en la API")
                self._log_data_load(dataset_name, "initial", 0, started_at, "success")
                return 0
            
            logger.info(f"Extraídos {len(records)} registros de la API")
            
            # Preparar datos para inserción
            insert_query = """
                INSERT INTO raw_homicidios (
                    fecha_hecho, cod_depto, departamento, cod_muni,
                    municipio, zona, sexo, cantidad, source_api
                ) VALUES %s
                ON CONFLICT DO NOTHING
            """
            
            # Convertir registros a tuplas
            values = [
                (
                    record.get("fecha_hecho"),
                    int(record.get("cod_depto")) if record.get("cod_depto") else None,
                    record.get("departamento"),
                    int(record.get("cod_muni")) if record.get("cod_muni") else None,
                    record.get("municipio"),
                    record.get("zona"),
                    record.get("sexo"),
                    int(record.get("cantidad", 1)),
                    "datos_abiertos_api"
                )
                for record in records
            ]
            
            # Insertar en lotes
            logger.info(f"Insertando {len(values)} registros en base de datos...")
            
            with self.db.get_cursor() as cursor:
                execute_values(cursor, insert_query, values, page_size=batch_size)
                inserted_count = cursor.rowcount
            
            logger.info(f"✅ Carga inicial completada: {inserted_count} registros insertados")
            
            # Registrar en log
            self._log_data_load(dataset_name, "initial", inserted_count, started_at, "success")
            
            return inserted_count
        
        except Exception as e:
            logger.error(f"❌ Error en carga inicial: {e}")
            self._log_data_load(dataset_name, "initial", 0, started_at, "failed", str(e))
            raise
    
    def load_homicidios_incremental(self, batch_size: int = 1000) -> int:
        """
        Carga incremental de homicidios (solo registros nuevos).
        
        Args:
            batch_size: Tamaño de lote para inserts
        
        Returns:
            Número de registros nuevos cargados
        """
        started_at = datetime.now()
        dataset_name = "raw_homicidios"
        
        logger.info("🔄 Iniciando carga incremental de homicidios")
        
        try:
            # Obtener última fecha cargada
            query_last_date = """
                SELECT MAX(fecha_hecho) as ultima_fecha
                FROM raw_homicidios
            """
            
            result = self.db.execute_query(query_last_date, fetch=True)
            ultima_fecha = result[0][0] if result and result[0][0] else None
            
            if not ultima_fecha:
                logger.warning("No hay datos previos, ejecutando carga inicial")
                return self.load_homicidios_initial(batch_size)
            
            logger.info(f"Última fecha en DB: {ultima_fecha}")
            
            # Extraer solo registros nuevos
            where_clause = f"fecha_hecho > '{ultima_fecha}'"
            
            logger.info(f"Extrayendo registros con filtro: {where_clause}")
            records = self.api_client.fetch_homicidios_paginated(
                page_size=batch_size,
                where_clause=where_clause
            )
            
            if not records:
                logger.info("No hay registros nuevos")
                self._log_data_load(dataset_name, "incremental", 0, started_at, "success")
                return 0
            
            logger.info(f"Extraídos {len(records)} registros nuevos")
            
            # Insertar registros
            insert_query = """
                INSERT INTO raw_homicidios (
                    fecha_hecho, cod_depto, departamento, cod_muni,
                    municipio, zona, sexo, cantidad, source_api
                ) VALUES %s
                ON CONFLICT DO NOTHING
            """
            
            values = [
                (
                    record.get("fecha_hecho"),
                    int(record.get("cod_depto")) if record.get("cod_depto") else None,
                    record.get("departamento"),
                    int(record.get("cod_muni")) if record.get("cod_muni") else None,
                    record.get("municipio"),
                    record.get("zona"),
                    record.get("sexo"),
                    int(record.get("cantidad", 1)),
                    "datos_abiertos_api"
                )
                for record in records
            ]
            
            with self.db.get_cursor() as cursor:
                execute_values(cursor, insert_query, values, page_size=batch_size)
                inserted_count = cursor.rowcount
            
            logger.info(f"✅ Carga incremental completada: {inserted_count} registros nuevos")
            
            self._log_data_load(dataset_name, "incremental", inserted_count, started_at, "success")
            
            return inserted_count
        
        except Exception as e:
            logger.error(f"❌ Error en carga incremental: {e}")
            self._log_data_load(dataset_name, "incremental", 0, started_at, "failed", str(e))
            raise
    
    def load_divipola_departamentos(self) -> int:
        """
        Carga única de departamentos DIVIPOLA.
        
        Returns:
            Número de departamentos cargados
        """
        started_at = datetime.now()
        dataset_name = "raw_divipola_departamentos"
        
        logger.info("🗺️  Iniciando carga de DIVIPOLA Departamentos")
        
        try:
            # Verificar si ya se cargó
            count_query = "SELECT COUNT(*) FROM raw_divipola_departamentos"
            result = self.db.execute_query(count_query, fetch=True)
            existing_count = result[0][0] if result else 0
            
            if existing_count > 0:
                logger.info(f"DIVIPOLA Departamentos ya cargado ({existing_count} registros)")
                return 0
            
            # Extraer de API
            records = self.api_client.fetch_divipola_departamentos()
            
            if not records:
                logger.warning("No se encontraron departamentos en la API")
                return 0
            
            logger.info(f"Extraídos {len(records)} departamentos")
            
            # Insertar
            insert_query = """
                INSERT INTO raw_divipola_departamentos (
                    cod_dpto, nom_dpto, latitud, longitud, geo_departamento, source_api
                ) VALUES %s
                ON CONFLICT (cod_dpto) DO NOTHING
            """
            
            values = [
                (
                    int(record.get("cod_dpto")) if record.get("cod_dpto") else None,
                    record.get("nom_dpto"),
                    float(record.get("latitud")) if record.get("latitud") else None,
                    float(record.get("longitud")) if record.get("longitud") else None,
                    str(record.get("geo_departamento")) if record.get("geo_departamento") else None,
                    "datos_abiertos_api"
                )
                for record in records
            ]
            
            with self.db.get_cursor() as cursor:
                execute_values(cursor, insert_query, values)
                inserted_count = cursor.rowcount
            
            logger.info(f"✅ Departamentos cargados: {inserted_count} registros")
            
            self._log_data_load(dataset_name, "full", inserted_count, started_at, "success")
            
            return inserted_count
        
        except Exception as e:
            logger.error(f"❌ Error cargando departamentos: {e}")
            self._log_data_load(dataset_name, "full", 0, started_at, "failed", str(e))
            raise
    
    def load_divipola_municipios(self) -> int:
        """
        Carga única de municipios DIVIPOLA.
        
        Returns:
            Número de municipios cargados
        """
        started_at = datetime.now()
        dataset_name = "raw_divipola_municipios"
        
        logger.info("🏘️  Iniciando carga de DIVIPOLA Municipios")
        
        try:
            # Verificar si ya se cargó
            count_query = "SELECT COUNT(*) FROM raw_divipola_municipios"
            result = self.db.execute_query(count_query, fetch=True)
            existing_count = result[0][0] if result else 0
            
            if existing_count > 0:
                logger.info(f"DIVIPOLA Municipios ya cargado ({existing_count} registros)")
                return 0
            
            # Extraer de API
            records = self.api_client.fetch_divipola_municipios()
            
            if not records:
                logger.warning("No se encontraron municipios en la API")
                return 0
            
            logger.info(f"Extraídos {len(records)} municipios")
            
            # Insertar
            insert_query = """
                INSERT INTO raw_divipola_municipios (
                    cod_dpto, nom_dpto, cod_mpio, nom_mpio, tipo,
                    latitud, longitud, geo_municipio, source_api
                ) VALUES %s
                ON CONFLICT (cod_mpio) DO NOTHING
            """
            
            values = [
                (
                    int(record.get("cod_dpto")) if record.get("cod_dpto") else None,
                    record.get("nom_dpto"),
                    int(record.get("cod_mpio")) if record.get("cod_mpio") else None,
                    record.get("nom_mpio"),
                    record.get("tipo"),
                    float(record.get("latitud")) if record.get("latitud") else None,
                    float(record.get("longitud")) if record.get("longitud") else None,
                    str(record.get("geo_municipio")) if record.get("geo_municipio") else None,
                    "datos_abiertos_api"
                )
                for record in records
            ]
            
            with self.db.get_cursor() as cursor:
                execute_values(cursor, insert_query, values, page_size=500)
                inserted_count = cursor.rowcount
            
            logger.info(f"✅ Municipios cargados: {inserted_count} registros")
            
            self._log_data_load(dataset_name, "full", inserted_count, started_at, "success")
            
            return inserted_count
        
        except Exception as e:
            logger.error(f"❌ Error cargando municipios: {e}")
            self._log_data_load(dataset_name, "full", 0, started_at, "failed", str(e))
            raise
    
    def load_all_initial(self) -> Dict[str, int]:
        """
        Ejecutar carga inicial de todos los datasets.
        
        Returns:
            Diccionario con conteo de registros por dataset
        """
        logger.info("=" * 70)
        logger.info("INICIANDO CARGA INICIAL COMPLETA")
        logger.info("=" * 70)
        
        results = {}
        
        try:
            # 1. Cargar DIVIPOLA (primero, son catálogos)
            results["departamentos"] = self.load_divipola_departamentos()
            results["municipios"] = self.load_divipola_municipios()
            
            # 2. Cargar homicidios
            results["homicidios"] = self.load_homicidios_initial()
            
            logger.info("=" * 70)
            logger.info("✅ CARGA INICIAL COMPLETADA")
            logger.info(f"   Departamentos: {results['departamentos']}")
            logger.info(f"   Municipios: {results['municipios']}")
            logger.info(f"   Homicidios: {results['homicidios']}")
            logger.info("=" * 70)
            
            return results
        
        except Exception as e:
            logger.error(f"❌ Error en carga inicial: {e}")
            raise
    
    def close(self):
        """Cerrar conexiones."""
        self.api_client.close()
        self.db.close_all_connections()
        logger.info("Conexiones cerradas")


if __name__ == "__main__":
    """Ejemplo de uso del cargador."""
    
    print("=" * 70)
    print("PRUEBA DE DATA LAKE LOADER")
    print("=" * 70)
    
    # Crear loader
    loader = DataLakeLoader()
    
    # Probar conexión
    print("\n🔌 Probando conexión a base de datos...")
    if not loader.db.test_connection():
        print("❌ No se pudo conectar a la base de datos")
        print("   Asegúrate de que Docker esté corriendo: docker-compose up -d")
        exit(1)
    
    print("✅ Conexión exitosa")
    
    # Aquí podrías ejecutar cargas de prueba
    # loader.load_all_initial()
    
    # Cerrar
    loader.close()
    
    print("\n" + "=" * 70)
