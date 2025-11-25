"""
Conexión al Data Warehouse.
Gestiona conexiones a PostgreSQL del DWH.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DWHConnection:
    """Gestor de conexiones al Data Warehouse."""
    
    def __init__(self):
        """Inicializar conexión al DWH."""
        self.conn_params = {
            'host': settings.dw_host,
            'port': settings.dw_port,
            'database': settings.dw_db,
            'user': settings.dw_user,
            'password': settings.dw_password
        }
        self._conn: Optional[psycopg2.extensions.connection] = None
        logger.info("DWHConnection inicializado")
    
    def connect(self) -> psycopg2.extensions.connection:
        """Crear conexión al DWH."""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**self.conn_params)
            logger.info("Conexión al Data Warehouse establecida")
        return self._conn
    
    def close(self):
        """Cerrar conexión."""
        if self._conn and not self._conn.closed:
            self._conn.close()
            logger.info("Conexión al Data Warehouse cerrada")
    
    @contextmanager
    def get_cursor(self, dict_cursor: bool = False):
        """
        Context manager para cursor.
        
        Args:
            dict_cursor: Si True, retorna RealDictCursor
        """
        conn = self.connect()
        cursor_factory = RealDictCursor if dict_cursor else None
        cursor = conn.cursor(cursor_factory=cursor_factory)
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error en transacción: {e}")
            raise
        finally:
            cursor.close()
    
    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch: bool = False,
        dict_cursor: bool = False
    ) -> Optional[List[Any]]:
        """
        Ejecutar query en DWH.
        
        Args:
            query: SQL query
            params: Parámetros para query
            fetch: Si True, retorna resultados
            dict_cursor: Si True, retorna diccionarios
        
        Returns:
            Resultados si fetch=True, None otherwise
        """
        with self.get_cursor(dict_cursor=dict_cursor) as cursor:
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            return None
    
    def execute_many(self, query: str, data: List[tuple]):
        """
        Ejecutar query con múltiples registros.
        
        Args:
            query: SQL query con placeholders
            data: Lista de tuplas con datos
        """
        with self.get_cursor() as cursor:
            cursor.executemany(query, data)
            logger.info(f"Ejecutados {len(data)} registros")
    
    def test_connection(self) -> bool:
        """Probar conexión al DWH."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result[0] == 1
        except Exception as e:
            logger.error(f"Error probando conexión: {e}")
            return False
