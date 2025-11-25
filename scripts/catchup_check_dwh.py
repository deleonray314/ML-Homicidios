"""
Script para verificar si hay cargas pendientes del Data Warehouse.
Detecta si se perdieron ejecuciones del ETL DWH.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_warehouse.dwh_connection import DWHConnection
from src.utils.logger import get_logger

logger = get_logger(__name__)


def verificar_cargas_pendientes_dwh() -> bool:
    """
    Verificar si hay cargas pendientes en el DWH.
    
    Returns:
        True si hay cargas pendientes, False si está al día
    """
    try:
        dwh = DWHConnection()
        
        # Obtener última carga exitosa
        query = """
            SELECT 
                MAX(completed_at) as ultima_carga,
                process_name
            FROM etl_log
            WHERE status = 'success'
            GROUP BY process_name
            ORDER BY MAX(completed_at) DESC
            LIMIT 1
        """
        
        result = dwh.execute_query(query, fetch=True, dict_cursor=True)
        
        if not result or not result[0]['ultima_carga']:
            logger.warning("⚠️ No hay cargas previas registradas en DWH")
            logger.info("💡 Se recomienda ejecutar carga inicial")
            return True
        
        ultima_carga = result[0]['ultima_carga']
        ahora = datetime.now()
        
        # Calcular días desde última carga
        dias_sin_carga = (ahora - ultima_carga).days
        
        logger.info(f"📅 Última carga DWH: {ultima_carga.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"📊 Días sin carga: {dias_sin_carga}")
        
        # Si han pasado más de 7 días (1 semana), hay cargas pendientes
        if dias_sin_carga > 7:
            logger.warning(f"⚠️ Han pasado {dias_sin_carga} días desde la última carga")
            logger.warning(f"💡 Se esperaba carga semanal (cada sábado)")
            logger.info("🔄 Se recomienda ejecutar carga incremental")
            return True
        
        # Verificar si es sábado y no se ha cargado hoy
        if ahora.weekday() == 5:  # 5 = Sábado
            if ultima_carga.date() < ahora.date():
                logger.info("📅 Es sábado y no se ha ejecutado carga hoy")
                logger.info("🔄 Se recomienda ejecutar carga incremental")
                return True
        
        # Verificar si pasó el sábado y no se cargó
        dias_desde_sabado = (ahora.weekday() - 5) % 7
        if dias_desde_sabado > 0 and dias_desde_sabado < 7:
            ultimo_sabado = ahora - timedelta(days=dias_desde_sabado)
            if ultima_carga.date() < ultimo_sabado.date():
                logger.warning(f"⚠️ No se ejecutó carga el sábado pasado ({ultimo_sabado.date()})")
                logger.info("🔄 Se recomienda ejecutar carga incremental")
                return True
        
        logger.info("✅ DWH al día, no hay cargas pendientes")
        return False
    
    except Exception as e:
        logger.error(f"❌ Error verificando cargas pendientes DWH: {e}")
        logger.exception("Detalles del error:")
        # En caso de error, mejor ejecutar carga por seguridad
        logger.warning("⚠️ Por seguridad, se recomienda ejecutar carga")
        return True
    
    finally:
        dwh.close()


def main():
    """Función principal."""
    logger.info("=" * 70)
    logger.info("VERIFICACIÓN DE CARGAS PENDIENTES - DATA WAREHOUSE")
    logger.info("=" * 70)
    
    hay_pendientes = verificar_cargas_pendientes_dwh()
    
    logger.info("=" * 70)
    
    if hay_pendientes:
        logger.info("🔴 Resultado: HAY CARGAS PENDIENTES EN DWH")
    else:
        logger.info("🟢 Resultado: DWH AL DÍA")
    
    logger.info("=" * 70)
    
    # Exit code: 1 = hay pendientes, 0 = todo al día
    return 1 if hay_pendientes else 0


if __name__ == "__main__":
    sys.exit(main())
