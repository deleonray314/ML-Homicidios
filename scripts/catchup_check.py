"""
Script para verificar si hay cargas pendientes.
Detecta si se perdieron ejecuciones del cron y necesita catch-up.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_ingestion.db_connection import DatabaseConnection
from src.utils.logger import get_logger

logger = get_logger(__name__)


def verificar_cargas_pendientes() -> bool:
    """
    Verificar si hay cargas pendientes.
    
    Returns:
        True si hay cargas pendientes, False si está al día
    """
    try:
        db = DatabaseConnection()
        
        # Obtener última carga exitosa de homicidios
        query = """
            SELECT 
                MAX(load_completed_at) as ultima_carga,
                dataset_name
            FROM data_load_log
            WHERE dataset_name = 'raw_homicidios'
                AND status = 'success'
            GROUP BY dataset_name
        """
        
        result = db.execute_query(query, fetch=True, dict_cursor=True)
        
        if not result or not result[0]['ultima_carga']:
            logger.warning("⚠️ No hay cargas previas registradas")
            logger.info("💡 Se recomienda ejecutar carga incremental")
            return True
        
        ultima_carga = result[0]['ultima_carga']
        ahora = datetime.now()
        
        # Calcular días desde última carga
        dias_sin_carga = (ahora - ultima_carga).days
        
        logger.info(f"📅 Última carga: {ultima_carga.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"📊 Días sin carga: {dias_sin_carga}")
        
        # Si han pasado más de 7 días (1 semana), hay cargas pendientes
        if dias_sin_carga > 7:
            logger.warning(f"⚠️ Han pasado {dias_sin_carga} días desde la última carga")
            logger.warning(f"💡 Se esperaba carga semanal (cada viernes)")
            logger.info("🔄 Se recomienda ejecutar carga incremental")
            return True
        
        # Verificar si es viernes y no se ha cargado hoy
        if ahora.weekday() == 4:  # 4 = Viernes
            if ultima_carga.date() < ahora.date():
                logger.info("📅 Es viernes y no se ha ejecutado carga hoy")
                logger.info("🔄 Se recomienda ejecutar carga incremental")
                return True
        
        # Verificar si pasó el viernes y no se cargó
        dias_desde_viernes = (ahora.weekday() - 4) % 7
        if dias_desde_viernes > 0 and dias_desde_viernes < 7:
            ultimo_viernes = ahora - timedelta(days=dias_desde_viernes)
            if ultima_carga.date() < ultimo_viernes.date():
                logger.warning(f"⚠️ No se ejecutó carga el viernes pasado ({ultimo_viernes.date()})")
                logger.info("🔄 Se recomienda ejecutar carga incremental")
                return True
        
        logger.info("✅ Sistema al día, no hay cargas pendientes")
        return False
    
    except Exception as e:
        logger.error(f"❌ Error verificando cargas pendientes: {e}")
        logger.exception("Detalles del error:")
        # En caso de error, mejor ejecutar carga por seguridad
        logger.warning("⚠️ Por seguridad, se recomienda ejecutar carga")
        return True
    
    finally:
        db.close_all_connections()


def main():
    """Función principal."""
    logger.info("=" * 70)
    logger.info("VERIFICACIÓN DE CARGAS PENDIENTES")
    logger.info("=" * 70)
    
    hay_pendientes = verificar_cargas_pendientes()
    
    logger.info("=" * 70)
    
    if hay_pendientes:
        logger.info("🔴 Resultado: HAY CARGAS PENDIENTES")
    else:
        logger.info("🟢 Resultado: SISTEMA AL DÍA")
    
    logger.info("=" * 70)
    
    # Exit code: 1 = hay pendientes, 0 = todo al día
    return 1 if hay_pendientes else 0


if __name__ == "__main__":
    sys.exit(main())
