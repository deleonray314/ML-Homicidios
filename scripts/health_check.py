"""
Health check para verificar estado del sistema ETL.
Verifica conexión a base de datos y últimas cargas.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_ingestion.db_connection import DatabaseConnection
from src.utils.logger import get_logger

logger = get_logger(__name__)


def verificar_conexion_db() -> bool:
    """Verificar conexión a Data Lake."""
    try:
        db = DatabaseConnection()
        if db.test_connection():
            logger.info("✅ Data Lake: Conexión OK")
            db.close_all_connections()
            return True
        else:
            logger.error("❌ Data Lake: Conexión FAILED")
            return False
    except Exception as e:
        logger.error(f"❌ Error conectando a Data Lake: {e}")
        return False


def verificar_ultimas_cargas():
    """Verificar últimas cargas registradas."""
    try:
        db = DatabaseConnection()
        
        query = """
            SELECT 
                dataset_name,
                load_type,
                load_completed_at,
                records_loaded,
                status
            FROM data_load_log
            ORDER BY load_completed_at DESC
            LIMIT 10
        """
        
        results = db.execute_query(query, fetch=True, dict_cursor=True)
        
        if not results:
            logger.warning("⚠️ No hay cargas registradas en el sistema")
            return
        
        logger.info(f"📊 Últimas {len(results)} cargas:")
        logger.info("-" * 70)
        
        for row in results:
            status_icon = "✅" if row['status'] == 'success' else "❌"
            logger.info(
                f"{status_icon} {row['dataset_name']:30} | "
                f"{row['load_type']:12} | "
                f"{row['records_loaded']:6} registros | "
                f"{row['load_completed_at'].strftime('%Y-%m-%d %H:%M')}"
            )
        
        db.close_all_connections()
        
    except Exception as e:
        logger.error(f"❌ Error verificando cargas: {e}")


def verificar_datos_recientes():
    """Verificar que hay datos recientes en homicidios."""
    try:
        db = DatabaseConnection()
        
        query = """
            SELECT 
                COUNT(*) as total_registros,
                MAX(fecha_hecho) as fecha_mas_reciente,
                MIN(fecha_hecho) as fecha_mas_antigua,
                MAX(loaded_at) as ultima_carga
            FROM raw_homicidios
        """
        
        result = db.execute_query(query, fetch=True, dict_cursor=True)
        
        if result and result[0]['total_registros']:
            row = result[0]
            logger.info("📈 Estadísticas de datos:")
            logger.info(f"   Total registros: {row['total_registros']:,}")
            logger.info(f"   Fecha más antigua: {row['fecha_mas_antigua']}")
            logger.info(f"   Fecha más reciente: {row['fecha_mas_reciente']}")
            logger.info(f"   Última carga: {row['ultima_carga'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Verificar si datos están actualizados
            dias_desde_ultima = (datetime.now().date() - row['fecha_mas_reciente']).days
            if dias_desde_ultima > 30:
                logger.warning(f"⚠️ Datos desactualizados: {dias_desde_ultima} días desde último registro")
            else:
                logger.info(f"✅ Datos actualizados: {dias_desde_ultima} días desde último registro")
        else:
            logger.warning("⚠️ No hay datos en raw_homicidios")
        
        db.close_all_connections()
        
    except Exception as e:
        logger.error(f"❌ Error verificando datos: {e}")


def main():
    """Función principal."""
    logger.info("=" * 70)
    logger.info("HEALTH CHECK - SISTEMA ETL")
    logger.info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    # 1. Verificar conexión
    logger.info("\n🔌 Verificando conexión a base de datos...")
    logger.info("-" * 70)
    conexion_ok = verificar_conexion_db()
    
    if not conexion_ok:
        logger.error("=" * 70)
        logger.error("❌ HEALTH CHECK FAILED: No hay conexión a base de datos")
        logger.error("=" * 70)
        return 1
    
    # 2. Verificar últimas cargas
    logger.info("\n📋 Verificando últimas cargas...")
    logger.info("-" * 70)
    verificar_ultimas_cargas()
    
    # 3. Verificar datos recientes
    logger.info("\n📊 Verificando datos en Data Lake...")
    logger.info("-" * 70)
    verificar_datos_recientes()
    
    # Resumen final
    logger.info("\n" + "=" * 70)
    logger.info("✅ HEALTH CHECK COMPLETADO")
    logger.info("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
