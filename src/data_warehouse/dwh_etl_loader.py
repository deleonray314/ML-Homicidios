"""
Data Warehouse ETL Loader.
Carga datos del Data Lake al Data Warehouse (modelo estrella).
"""

from datetime import datetime, date
from typing import Optional, Dict, List
from uuid import UUID

from src.data_ingestion.db_connection import DatabaseConnection
from src.data_warehouse.dwh_connection import DWHConnection
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DWHETLLoader:
    """Cargador ETL para Data Warehouse."""
    
    def __init__(self):
        """Inicializar loader."""
        self.datalake = DatabaseConnection()  # Conexión al Data Lake
        self.dwh = DWHConnection()  # Conexión al Data Warehouse
        logger.info("DWHETLLoader inicializado")
    
    # ========================================================================
    # DIMENSIONES
    # ========================================================================
    
    def load_dim_departamento(self) -> int:
        """
        Cargar dimensión de departamentos desde Data Lake.
        
        Returns:
            Número de registros cargados
        """
        logger.info("Cargando dim_departamento...")
        
        # Extraer departamentos únicos del Data Lake
        query_extract = """
            SELECT DISTINCT
                cod_dpto as cod_depto,
                nom_dpto as nom_depto,
                latitud as depto_latitud,
                longitud as depto_longitud
            FROM raw_divipola_departamentos
            ORDER BY cod_dpto
        """
        
        departamentos = self.datalake.execute_query(
            query_extract,
            fetch=True,
            dict_cursor=True
        )
        
        if not departamentos:
            logger.warning("No hay departamentos en Data Lake")
            return 0
        
        # Insertar en DWH (UPSERT)
        query_insert = """
            INSERT INTO dim_departamento (cod_depto, nom_depto, latitud, longitud)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (cod_depto) DO UPDATE SET
                nom_depto = EXCLUDED.nom_depto,
                latitud = EXCLUDED.latitud,
                longitud = EXCLUDED.longitud
        """
        
        data = [
            (
                d['cod_depto'],
                d['nom_depto'],
                d['depto_latitud'],
                d['depto_longitud']
            )
            for d in departamentos
        ]
        
        self.dwh.execute_many(query_insert, data)
        
        logger.info(f"✅ dim_departamento: {len(data)} registros cargados")
        return len(data)
    
    def load_dim_municipio(self) -> int:
        """
        Cargar dimensión de municipios desde Data Lake.
        
        Returns:
            Número de registros cargados
        """
        logger.info("Cargando dim_municipio...")
        
        # Extraer municipios del Data Lake
        query_extract = """
            SELECT DISTINCT
                cod_mpio,
                cod_dpto as cod_depto,
                nom_mpio,
                tipo as tipo_mpio,
                latitud as mpio_latitud,
                longitud as mpio_longitud
            FROM raw_divipola_municipios
            ORDER BY cod_mpio
        """
        
        municipios = self.datalake.execute_query(
            query_extract,
            fetch=True,
            dict_cursor=True
        )
        
        if not municipios:
            logger.warning("No hay municipios en Data Lake")
            return 0
        
        # Insertar en DWH (UPSERT)
        query_insert = """
            INSERT INTO dim_municipio (cod_mpio, cod_depto, nom_mpio, tipo, latitud, longitud)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (cod_mpio) DO UPDATE SET
                cod_depto = EXCLUDED.cod_depto,
                nom_mpio = EXCLUDED.nom_mpio,
                tipo = EXCLUDED.tipo,
                latitud = EXCLUDED.latitud,
                longitud = EXCLUDED.longitud
        """
        
        data = [
            (
                m['cod_mpio'],
                m['cod_depto'],
                m['nom_mpio'],
                m['tipo_mpio'],
                m['mpio_latitud'],
                m['mpio_longitud']
            )
            for m in municipios
        ]
        
        self.dwh.execute_many(query_insert, data)
        
        logger.info(f"✅ dim_municipio: {len(data)} registros cargados")
        return len(data)
    
    def load_dim_sexo(self) -> int:
        """
        Cargar dimensión de sexo desde Data Lake.
        
        Returns:
            Número de registros cargados
        """
        logger.info("Cargando dim_sexo...")
        
        # Extraer sexos únicos del Data Lake
        query_extract = """
            SELECT DISTINCT sexo
            FROM raw_homicidios
            WHERE sexo IS NOT NULL
            ORDER BY sexo
        """
        
        sexos = self.datalake.execute_query(query_extract, fetch=True, dict_cursor=False)
        
        if not sexos:
            logger.warning("No hay sexos en Data Lake")
            return 0
        
        # Insertar en DWH (UPSERT)
        query_insert = """
            INSERT INTO dim_sexo (sexo)
            VALUES (%s)
            ON CONFLICT (sexo) DO NOTHING
        """
        
        # Manejar tanto tuplas como dicts
        data = []
        for s in sexos:
            if isinstance(s, dict):
                data.append((s['sexo'],))
            elif isinstance(s, tuple):
                data.append((s[0],))
            else:
                data.append((str(s),))
        
        self.dwh.execute_many(query_insert, data)
        
        logger.info(f"✅ dim_sexo: {len(data)} registros cargados")
        return len(data)
    
    def load_dim_fecha(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> int:
        """
        Cargar dimensión de fechas.
        Genera fechas desde start_date hasta end_date.
        
        Args:
            start_date: Fecha inicial (default: fecha mínima en homicidios)
            end_date: Fecha final (default: fecha máxima en homicidios)
        
        Returns:
            Número de registros cargados
        """
        logger.info("Cargando dim_fecha...")
        
        # Si no se especifican fechas, obtener del Data Lake
        if not start_date or not end_date:
            query_dates = """
                SELECT 
                    MIN(fecha_hecho) as min_fecha,
                    MAX(fecha_hecho) as max_fecha
                FROM raw_homicidios
            """
            result = self.datalake.execute_query(query_dates, fetch=True, dict_cursor=True)
            
            if result and len(result) > 0:
                row = result[0]
                start_date = row['min_fecha'] if row['min_fecha'] else date(2000, 1, 1)
                end_date = row['max_fecha'] if row['max_fecha'] else date.today()
            else:
                start_date = date(2000, 1, 1)
                end_date = date.today()
        
        logger.info(f"Generando fechas desde {start_date} hasta {end_date}")
        
        # Generar todas las fechas en el rango
        from datetime import timedelta
        
        current_date = start_date
        fechas_data = []
        
        while current_date <= end_date:
            # Calcular atributos de fecha
            año = current_date.year
            mes = current_date.month
            dia = current_date.day
            trimestre = (mes - 1) // 3 + 1
            semana_año = current_date.isocalendar()[1]
            dia_semana = current_date.isoweekday()  # 1=Lunes, 7=Domingo
            
            # Nombres
            nombres_mes = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                          'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
            nombres_dia = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            
            nombre_mes = nombres_mes[mes - 1]
            nombre_dia_semana = nombres_dia[dia_semana - 1]
            
            # Flags
            es_fin_semana = dia_semana in [6, 7]  # Sábado o Domingo
            
            fechas_data.append((
                current_date,
                año,
                mes,
                dia,
                trimestre,
                semana_año,
                dia_semana,
                nombre_mes,
                nombre_dia_semana,
                es_fin_semana
            ))
            
            current_date += timedelta(days=1)
        
        # Insertar en DWH (UPSERT)
        query_insert = """
            INSERT INTO dim_fecha (
                fecha, año, mes, dia, trimestre, semana_año, dia_semana,
                nombre_mes, nombre_dia_semana, es_fin_semana
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (fecha) DO NOTHING
        """
        
        self.dwh.execute_many(query_insert, fechas_data)
        
        logger.info(f"✅ dim_fecha: {len(fechas_data)} registros cargados")
        return len(fechas_data)
    
    # ========================================================================
    # TABLA DE HECHOS
    # ========================================================================
    
    def load_fact_homicidios_initial(self, batch_size: int = 5000) -> int:
        """
        Carga inicial completa de fact_homicidios.
        
        Args:
            batch_size: Tamaño de lote para inserts
        
        Returns:
            Número de registros cargados
        """
        logger.info("🔄 Carga inicial de fact_homicidios...")
        
        # Extraer homicidios del Data Lake
        query_extract = """
            SELECT 
                id,
                fecha_hecho,
                cod_depto,
                cod_muni,
                sexo,
                zona,
                cantidad
            FROM raw_homicidios
            ORDER BY fecha_hecho, id
        """
        
        homicidios = self.datalake.execute_query(
            query_extract,
            fetch=True,
            dict_cursor=True
        )
        
        if not homicidios:
            logger.warning("No hay homicidios en Data Lake")
            return 0
        
        logger.info(f"Extraídos {len(homicidios)} registros del Data Lake")
        
        # Cargar en batches
        total_loaded = 0
        
        for i in range(0, len(homicidios), batch_size):
            batch = homicidios[i:i + batch_size]
            loaded = self._load_fact_batch(batch)
            total_loaded += loaded
            logger.info(f"Batch {i//batch_size + 1}: {loaded} registros cargados")
        
        logger.info(f"✅ fact_homicidios: {total_loaded} registros cargados")
        return total_loaded
    
    def load_fact_homicidios_incremental(self) -> int:
        """
        Carga incremental de fact_homicidios.
        Solo carga registros nuevos desde la última carga.
        
        Returns:
            Número de registros cargados
        """
        logger.info("🔄 Carga incremental de fact_homicidios...")
        
        # Obtener última fecha cargada en DWH
        query_last_date = """
            SELECT MAX(f.loaded_at) as ultima_carga
            FROM fact_homicidios f
        """
        
        result = self.dwh.execute_query(query_last_date, fetch=True)
        ultima_carga = result[0][0] if result and result[0][0] else datetime(2000, 1, 1)
        
        logger.info(f"Última carga en DWH: {ultima_carga}")
        
        # Extraer solo registros nuevos del Data Lake
        query_extract = """
            SELECT 
                id,
                fecha_hecho,
                cod_depto,
                cod_muni,
                sexo,
                zona,
                cantidad
            FROM raw_homicidios
            WHERE loaded_at > %s
            ORDER BY fecha_hecho, id
        """
        
        homicidios = self.datalake.execute_query(
            query_extract,
            params=(ultima_carga,),
            fetch=True,
            dict_cursor=True
        )
        
        if not homicidios:
            logger.info("✅ No hay registros nuevos para cargar")
            return 0
        
        logger.info(f"Extraídos {len(homicidios)} registros nuevos")
        
        # Cargar batch
        loaded = self._load_fact_batch(homicidios)
        
        logger.info(f"✅ fact_homicidios incremental: {loaded} registros cargados")
        return loaded
    
    def _load_fact_batch(self, homicidios: List[Dict]) -> int:
        """
        Cargar un batch de homicidios a fact table.
        
        Args:
            homicidios: Lista de registros de homicidios
        
        Returns:
            Número de registros cargados
        """
        # Obtener mapeos de dimensiones
        fecha_keys = self._get_fecha_keys()
        sexo_keys = self._get_sexo_keys()
        
        # Preparar datos para inserción
        fact_data = []
        
        for h in homicidios:
            # Lookup de keys
            fecha_key = fecha_keys.get(h['fecha_hecho'])
            sexo_key = sexo_keys.get(h['sexo'])
            
            if not fecha_key:
                logger.warning(f"Fecha no encontrada en dim_fecha: {h['fecha_hecho']}")
                continue
            
            if not sexo_key:
                logger.warning(f"Sexo no encontrado en dim_sexo: {h['sexo']}")
                continue
            
            fact_data.append((
                fecha_key,
                h['cod_depto'],
                h['cod_muni'],
                sexo_key,
                h['zona'],
                h['cantidad'] or 1,
                h['id']  # source_id
            ))
        
        if not fact_data:
            return 0
        
        # Insertar en fact table
        query_insert = """
            INSERT INTO fact_homicidios (
                fecha_key, cod_depto, cod_mpio, sexo_key, zona, cantidad, source_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """
        
        self.dwh.execute_many(query_insert, fact_data)
        
        return len(fact_data)
    
    def _get_fecha_keys(self) -> Dict[date, int]:
        """Obtener mapeo de fecha -> fecha_key."""
        query = "SELECT fecha_key, fecha FROM dim_fecha"
        results = self.dwh.execute_query(query, fetch=True)
        return {row[1]: row[0] for row in results}
    
    def _get_sexo_keys(self) -> Dict[str, int]:
        """Obtener mapeo de sexo -> sexo_key."""
        query = "SELECT sexo_key, sexo FROM dim_sexo"
        results = self.dwh.execute_query(query, fetch=True)
        return {row[1]: row[0] for row in results}
    
    # ========================================================================
    # ORQUESTACIÓN
    # ========================================================================
    
    def load_all_initial(self) -> Dict[str, int]:
        """
        Carga inicial completa del DWH.
        Carga todas las dimensiones y luego la tabla de hechos.
        
        Returns:
            Diccionario con conteo de registros por tabla
        """
        logger.info("=" * 70)
        logger.info("CARGA INICIAL COMPLETA DEL DATA WAREHOUSE")
        logger.info("=" * 70)
        
        started_at = datetime.now()
        results = {}
        
        try:
            # 1. Cargar dimensiones (orden importante por FKs)
            results['dim_departamento'] = self.load_dim_departamento()
            results['dim_municipio'] = self.load_dim_municipio()
            results['dim_sexo'] = self.load_dim_sexo()
            results['dim_fecha'] = self.load_dim_fecha()
            
            # 2. Cargar tabla de hechos
            results['fact_homicidios'] = self.load_fact_homicidios_initial()
            
            # 3. Log de auditoría
            self._log_etl_process('initial_load', results, started_at, 'success')
            
            logger.info("=" * 70)
            logger.info("✅ CARGA INICIAL COMPLETADA")
            logger.info(f"Tiempo total: {datetime.now() - started_at}")
            logger.info("=" * 70)
            
            return results
        
        except Exception as e:
            logger.error(f"❌ Error en carga inicial: {e}")
            self._log_etl_process('initial_load', results, started_at, 'failed', str(e))
            raise
    
    def load_incremental(self) -> Dict[str, int]:
        """
        Carga incremental del DWH.
        Actualiza dimensiones y carga nuevos hechos.
        
        Returns:
            Diccionario con conteo de registros por tabla
        """
        logger.info("=" * 70)
        logger.info("CARGA INCREMENTAL DEL DATA WAREHOUSE")
        logger.info("=" * 70)
        
        started_at = datetime.now()
        results = {}
        
        try:
            # 1. Actualizar dimensiones (por si hay nuevos valores)
            results['dim_departamento'] = self.load_dim_departamento()
            results['dim_municipio'] = self.load_dim_municipio()
            results['dim_sexo'] = self.load_dim_sexo()
            results['dim_fecha'] = self.load_dim_fecha()  # Solo agrega fechas nuevas
            
            # 2. Cargar hechos incrementales
            results['fact_homicidios'] = self.load_fact_homicidios_incremental()
            
            # 3. Log de auditoría
            self._log_etl_process('incremental_load', results, started_at, 'success')
            
            logger.info("=" * 70)
            logger.info("✅ CARGA INCREMENTAL COMPLETADA")
            logger.info(f"Tiempo total: {datetime.now() - started_at}")
            logger.info("=" * 70)
            
            return results
        
        except Exception as e:
            logger.error(f"❌ Error en carga incremental: {e}")
            self._log_etl_process('incremental_load', results, started_at, 'failed', str(e))
            raise
    
    def _log_etl_process(
        self,
        process_name: str,
        results: Dict[str, int],
        started_at: datetime,
        status: str,
        error_message: Optional[str] = None
    ):
        """Registrar proceso ETL en tabla de auditoría."""
        total_processed = sum(results.values())
        
        query = """
            INSERT INTO etl_log (
                process_name, records_processed, records_inserted, records_updated,
                started_at, status, error_message
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        self.dwh.execute_query(
            query,
            params=(
                process_name,
                total_processed,
                total_processed,  # Para simplificar, asumimos todos insertados
                0,
                started_at,
                status,
                error_message
            )
        )
    
    def close(self):
        """Cerrar todas las conexiones."""
        self.datalake.close_all_connections()
        self.dwh.close()
        logger.info("Conexiones cerradas")
