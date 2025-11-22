"""
Gestor de conexiones a PostgreSQL para el Data Lake.

Proporciona pool de conexiones, context managers y manejo de transacciones.
"""

from contextlib import contextmanager
from typing import Optional, Generator
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseConnection:
    """Gestor de conexiones a PostgreSQL con pool de conexiones."""
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        min_connections: int = 1,
        max_connections: int = 10
    ):
        """
        Inicializar gestor de conexiones.
        
        Args:
            host: Host de PostgreSQL (usa settings si es None)
            port: Puerto de PostgreSQL
            database: Nombre de la base de datos
            user: Usuario
            password: Contraseña
            min_connections: Mínimo de conexiones en el pool
            max_connections: Máximo de conexiones en el pool
        """
        # Usar valores de .env si no se especifican
        self.host = host or settings.db_host
        self.port = port or settings.db_port
        self.database = database or settings.db_name
        self.user = user or settings.db_user
        self.password = password or settings.db_password
        
        self.connection_pool: Optional[pool.SimpleConnectionPool] = None
        self.min_connections = min_connections
        self.max_connections = max_connections
        
        logger.info(f"Inicializando conexión a PostgreSQL: {self.host}:{self.port}/{self.database}")
    
    def _create_pool(self):
        """Crear pool de conexiones."""
        try:
            self.connection_pool = pool.SimpleConnectionPool(
                self.min_connections,
                self.max_connections,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            logger.info(f"Pool de conexiones creado ({self.min_connections}-{self.max_connections})")
        except psycopg2.Error as e:
            logger.error(f"Error creando pool de conexiones: {e}")
            raise
    
    def get_pool(self) -> pool.SimpleConnectionPool:
        """
        Obtener pool de conexiones (crear si no existe).
        
        Returns:
            Pool de conexiones
        """
        if self.connection_pool is None:
            self._create_pool()
        return self.connection_pool
    
    @contextmanager
    def get_connection(self, dict_cursor: bool = False) -> Generator:
        """
        Context manager para obtener una conexión del pool.
        
        Args:
            dict_cursor: Si True, usar RealDictCursor (resultados como dict)
        
        Yields:
            Conexión de PostgreSQL
        
        Example:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM table")
        """
        pool = self.get_pool()
        conn = None
        
        try:
            conn = pool.getconn()
            
            if dict_cursor:
                conn.cursor_factory = RealDictCursor
            
            logger.debug("Conexión obtenida del pool")
            yield conn
            
        except psycopg2.Error as e:
            logger.error(f"Error en conexión: {e}")
            if conn:
                conn.rollback()
            raise
        
        finally:
            if conn:
                pool.putconn(conn)
                logger.debug("Conexión devuelta al pool")
    
    @contextmanager
    def get_cursor(self, dict_cursor: bool = False) -> Generator:
        """
        Context manager para obtener un cursor directamente.
        
        Args:
            dict_cursor: Si True, usar RealDictCursor
        
        Yields:
            Cursor de PostgreSQL
        
        Example:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM table")
                results = cursor.fetchall()
        """
        with self.get_connection(dict_cursor=dict_cursor) as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Error en cursor, rollback ejecutado: {e}")
                raise
            finally:
                cursor.close()
    
    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch: bool = False,
        dict_cursor: bool = False
    ):
        """
        Ejecutar una query SQL.
        
        Args:
            query: Query SQL
            params: Parámetros para la query
            fetch: Si True, retornar resultados
            dict_cursor: Si True, retornar resultados como dict
        
        Returns:
            Resultados si fetch=True, None en caso contrario
        """
        with self.get_cursor(dict_cursor=dict_cursor) as cursor:
            cursor.execute(query, params)
            
            if fetch:
                return cursor.fetchall()
            
            return None
    
    def execute_many(
        self,
        query: str,
        data: list
    ):
        """
        Ejecutar query con múltiples sets de parámetros (INSERT batch).
        
        Args:
            query: Query SQL con placeholders
            data: Lista de tuplas con parámetros
        
        Example:
            query = "INSERT INTO table (col1, col2) VALUES (%s, %s)"
            data = [(1, 'a'), (2, 'b'), (3, 'c')]
            db.execute_many(query, data)
        """
        with self.get_cursor() as cursor:
            cursor.executemany(query, data)
            logger.info(f"Ejecutados {len(data)} inserts en batch")
    
    def test_connection(self) -> bool:
        """
        Probar conexión a la base de datos.
        
        Returns:
            True si la conexión es exitosa
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
                if result and result[0] == 1:
                    logger.info("✅ Conexión a base de datos exitosa")
                    return True
                
                return False
        
        except Exception as e:
            logger.error(f"❌ Error en conexión a base de datos: {e}")
            return False
    
    def close_all_connections(self):
        """Cerrar todas las conexiones del pool."""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Todas las conexiones cerradas")
            self.connection_pool = None


# Instancia global para Data Lake
datalake_db = DatabaseConnection(
    host=settings.db_host,
    port=settings.db_port,
    database=settings.db_name,
    user=settings.db_user,
    password=settings.db_password
)


if __name__ == "__main__":
    """Ejemplo de uso de DatabaseConnection."""
    
    print("=" * 70)
    print("PRUEBA DE CONEXIÓN A BASE DE DATOS")
    print("=" * 70)
    
    # Crear conexión
    db = DatabaseConnection()
    
    # Probar conexión
    print("\n🔌 Probando conexión...")
    if db.test_connection():
        print("✅ Conexión exitosa")
    else:
        print("❌ Conexión fallida")
        exit(1)
    
    # Probar query simple
    print("\n📊 Ejecutando query de prueba...")
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            
            print(f"✅ Tablas encontradas: {len(tables)}")
            for table in tables:
                print(f"   - {table[0]}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Cerrar conexiones
    print("\n🔒 Cerrando conexiones...")
    db.close_all_connections()
    print("✅ Conexiones cerradas")
    
    print("\n" + "=" * 70)
