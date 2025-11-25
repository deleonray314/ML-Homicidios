"""
Script de orquestación para ETL del Data Warehouse.
Carga datos del Data Lake al Data Warehouse (modelo estrella).
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_warehouse.dwh_etl_loader import DWHETLLoader
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="ETL del Data Warehouse - Carga datos desde Data Lake"
    )
    
    parser.add_argument(
        "--initial",
        action="store_true",
        help="Ejecutar carga inicial completa"
    )
    
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Ejecutar carga incremental (solo registros nuevos)"
    )
    
    args = parser.parse_args()
    
    # Validar argumentos
    if not args.initial and not args.incremental:
        parser.error("Debes especificar --initial o --incremental")
    
    if args.initial and args.incremental:
        parser.error("No puedes usar --initial y --incremental al mismo tiempo")
    
    # Crear loader
    logger.info("=" * 70)
    logger.info("INICIANDO ETL DEL DATA WAREHOUSE")
    logger.info("=" * 70)
    
    loader = DWHETLLoader()
    
    # Verificar conexiones
    logger.info("Verificando conexiones...")
    
    if not loader.datalake.test_connection():
        logger.error("❌ No se pudo conectar al Data Lake")
        sys.exit(1)
    
    if not loader.dwh.test_connection():
        logger.error("❌ No se pudo conectar al Data Warehouse")
        sys.exit(1)
    
    logger.info("✅ Conexiones verificadas")
    
    try:
        # Ejecutar carga según argumentos
        if args.initial:
            logger.info("🔄 Ejecutando CARGA INICIAL...")
            results = loader.load_all_initial()
            
            logger.info("=" * 70)
            logger.info("RESUMEN DE CARGA INICIAL:")
            for table, count in results.items():
                logger.info(f"  {table}: {count:,} registros")
            logger.info("=" * 70)
        
        elif args.incremental:
            logger.info("🔄 Ejecutando CARGA INCREMENTAL...")
            results = loader.load_incremental()
            
            logger.info("=" * 70)
            logger.info("RESUMEN DE CARGA INCREMENTAL:")
            for table, count in results.items():
                logger.info(f"  {table}: {count:,} registros")
            logger.info("=" * 70)
        
        logger.info("✅ PROCESO COMPLETADO EXITOSAMENTE")
        
    except Exception as e:
        logger.error("=" * 70)
        logger.error(f"❌ ERROR EN PROCESO: {e}")
        logger.error("=" * 70)
        logger.exception("Detalles del error:")
        sys.exit(1)
    
    finally:
        # Cerrar conexiones
        loader.close()


if __name__ == "__main__":
    main()
