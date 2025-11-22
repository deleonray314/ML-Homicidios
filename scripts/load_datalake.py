#!/usr/bin/env python
"""
Script principal para cargar datos al Data Lake.

Uso:
    # Carga inicial completa
    python scripts/load_datalake.py --initial

    # Carga incremental
    python scripts/load_datalake.py --incremental

    # Cargar solo un dataset específico
    python scripts/load_datalake.py --dataset homicidios --initial
    python scripts/load_datalake.py --dataset departamentos
    python scripts/load_datalake.py --dataset municipios
"""

import argparse
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_ingestion.data_lake_loader import DataLakeLoader
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Cargar datos al Data Lake desde API de Datos Abiertos"
    )
    
    # Argumentos
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
    
    parser.add_argument(
        "--dataset",
        choices=["homicidios", "departamentos", "municipios", "all"],
        help="Dataset específico a cargar"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Tamaño de lote para inserts (default: 1000)"
    )
    
    args = parser.parse_args()
    
    # Validar argumentos
    if not args.initial and not args.incremental and not args.dataset:
        parser.error("Debes especificar --initial, --incremental, o --dataset")
    
    if args.initial and args.incremental:
        parser.error("No puedes usar --initial y --incremental al mismo tiempo")
    
    # Crear loader
    logger.info("=" * 70)
    logger.info("INICIANDO CARGA DE DATA LAKE")
    logger.info("=" * 70)
    
    loader = DataLakeLoader()
    
    # Verificar conexión
    logger.info("Verificando conexión a base de datos...")
    if not loader.db.test_connection():
        logger.error("❌ No se pudo conectar a la base de datos")
        logger.error("   Asegúrate de que Docker esté corriendo: docker-compose up -d")
        sys.exit(1)
    
    logger.info("✅ Conexión exitosa")
    
    try:
        # Ejecutar carga según argumentos
        if args.dataset:
            # Cargar dataset específico
            if args.dataset == "homicidios":
                if args.initial:
                    count = loader.load_homicidios_initial(args.batch_size)
                elif args.incremental:
                    count = loader.load_homicidios_incremental(args.batch_size)
                else:
                    # Por defecto, incremental
                    count = loader.load_homicidios_incremental(args.batch_size)
                
                logger.info(f"✅ Homicidios: {count} registros cargados")
            
            elif args.dataset == "departamentos":
                count = loader.load_divipola_departamentos()
                logger.info(f"✅ Departamentos: {count} registros cargados")
            
            elif args.dataset == "municipios":
                count = loader.load_divipola_municipios()
                logger.info(f"✅ Municipios: {count} registros cargados")
            
            elif args.dataset == "all":
                results = loader.load_all_initial()
                logger.info("✅ Todos los datasets cargados:")
                for dataset, count in results.items():
                    logger.info(f"   {dataset}: {count} registros")
        
        elif args.initial:
            # Carga inicial de todo
            results = loader.load_all_initial()
            logger.info("✅ Carga inicial completada:")
            for dataset, count in results.items():
                logger.info(f"   {dataset}: {count} registros")
        
        elif args.incremental:
            # Carga incremental de homicidios
            count = loader.load_homicidios_incremental(args.batch_size)
            logger.info(f"✅ Carga incremental: {count} registros nuevos")
        
        logger.info("=" * 70)
        logger.info("✅ PROCESO COMPLETADO EXITOSAMENTE")
        logger.info("=" * 70)
    
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
