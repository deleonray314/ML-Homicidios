"""
Cliente para la API SODA de Datos Abiertos Colombia.

Maneja la extracción de datos de los 3 datasets:
- Homicidios (con soporte para carga incremental)
- DIVIPOLA Departamentos (carga única)
- DIVIPOLA Municipios (carga única)
"""

import time
from typing import Dict, List, Optional, Any
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DatosAbiertosClient:
    """Cliente para interactuar con la API SODA de Datos Abiertos Colombia."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializar cliente de API.
        
        Args:
            api_key: API key opcional (mejora rate limits)
        """
        self.api_key = api_key or settings.api_key
        self.base_url = settings.base_url
        self.session = self._create_session()
        
        logger.info("Cliente de API inicializado", extra={
            "extra_fields": {"base_url": self.base_url}
        })
    
    def _create_session(self) -> requests.Session:
        """
        Crear sesión HTTP con retry logic.
        
        Returns:
            Sesión configurada con reintentos automáticos
        """
        session = requests.Session()
        
        # Configurar reintentos automáticos
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Headers por defecto
        session.headers.update({
            "User-Agent": "ML-Homicidios/1.0",
            "Accept": "application/json"
        })
        
        # Agregar API key si existe
        if self.api_key:
            session.headers.update({"X-App-Token": self.api_key})
        
        return session
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Hacer request a la API con manejo de errores.
        
        Args:
            endpoint: URL del endpoint
            params: Parámetros de query
        
        Returns:
            Lista de registros
        
        Raises:
            requests.RequestException: Si falla el request
        """
        try:
            logger.debug(f"Request a {endpoint}", extra={
                "extra_fields": {"params": params}
            })
            
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            logger.debug(f"Recibidos {len(data)} registros")
            
            return data
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en request a API: {e}", extra={
                "extra_fields": {"endpoint": endpoint, "params": params}
            })
            raise
    
    def fetch_homicidios(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        where_clause: Optional[str] = None,
        order_by: str = "fecha_hecho"
    ) -> List[Dict[str, Any]]:
        """
        Extraer datos de homicidios con paginación.
        
        Args:
            limit: Número máximo de registros (None = todos)
            offset: Offset para paginación
            where_clause: Filtro SQL (ej: "fecha_hecho > '2024-01-01'")
            order_by: Campo para ordenar
        
        Returns:
            Lista de registros de homicidios
        """
        endpoint = settings.get_api_endpoint("homicidios")
        
        params = {
            "$order": order_by,
            "$offset": offset
        }
        
        if limit:
            params["$limit"] = limit
        
        if where_clause:
            params["$where"] = where_clause
        
        logger.info(f"Extrayendo homicidios", extra={
            "extra_fields": {
                "limit": limit,
                "offset": offset,
                "where": where_clause
            }
        })
        
        return self._make_request(endpoint, params)
    
    def fetch_homicidios_paginated(
        self,
        page_size: int = 1000,
        where_clause: Optional[str] = None,
        max_records: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extraer todos los homicidios con paginación automática.
        
        Args:
            page_size: Tamaño de cada página
            where_clause: Filtro SQL
            max_records: Máximo de registros a extraer (None = todos)
        
        Returns:
            Lista completa de registros
        """
        all_records = []
        offset = 0
        
        logger.info(f"Iniciando extracción paginada de homicidios")
        
        while True:
            # Calcular limit para esta página
            if max_records:
                remaining = max_records - len(all_records)
                current_limit = min(page_size, remaining)
                if current_limit <= 0:
                    break
            else:
                current_limit = page_size
            
            # Extraer página
            records = self.fetch_homicidios(
                limit=current_limit,
                offset=offset,
                where_clause=where_clause
            )
            
            if not records:
                break
            
            all_records.extend(records)
            offset += len(records)
            
            logger.info(f"Extraídos {len(all_records)} registros hasta ahora")
            
            # Si recibimos menos registros que el límite, es la última página
            if len(records) < page_size:
                break
            
            # Rate limiting (evitar sobrecargar la API)
            time.sleep(0.5)
        
        logger.info(f"Extracción completada: {len(all_records)} registros totales")
        
        return all_records
    
    def fetch_divipola_departamentos(self) -> List[Dict[str, Any]]:
        """
        Extraer catálogo completo de departamentos DIVIPOLA.
        
        Returns:
            Lista de departamentos
        """
        endpoint = settings.get_api_endpoint("departamentos")
        
        logger.info("Extrayendo DIVIPOLA Departamentos")
        
        # DIVIPOLA es un catálogo pequeño, extraer todo de una vez
        params = {"$limit": 50}  # Colombia tiene 32 departamentos
        
        records = self._make_request(endpoint, params)
        
        logger.info(f"Extraídos {len(records)} departamentos")
        
        return records
    
    def fetch_divipola_municipios(self) -> List[Dict[str, Any]]:
        """
        Extraer catálogo completo de municipios DIVIPOLA.
        
        Returns:
            Lista de municipios
        """
        endpoint = settings.get_api_endpoint("municipios")
        
        logger.info("Extrayendo DIVIPOLA Municipios")
        
        # Colombia tiene ~1100 municipios, usar paginación
        all_records = []
        offset = 0
        page_size = 1000
        
        while True:
            params = {
                "$limit": page_size,
                "$offset": offset
            }
            
            records = self._make_request(endpoint, params)
            
            if not records:
                break
            
            all_records.extend(records)
            offset += len(records)
            
            if len(records) < page_size:
                break
        
        logger.info(f"Extraídos {len(all_records)} municipios")
        
        return all_records
    
    def get_latest_fecha_hecho(self) -> Optional[str]:
        """
        Obtener la fecha más reciente de homicidios en la API.
        
        Returns:
            Fecha más reciente en formato ISO (YYYY-MM-DD) o None
        """
        try:
            endpoint = settings.get_api_endpoint("homicidios")
            
            params = {
                "$select": "fecha_hecho",
                "$order": "fecha_hecho DESC",
                "$limit": 1
            }
            
            records = self._make_request(endpoint, params)
            
            if records and "fecha_hecho" in records[0]:
                fecha = records[0]["fecha_hecho"]
                logger.info(f"Fecha más reciente en API: {fecha}")
                return fecha
            
            return None
        
        except Exception as e:
            logger.error(f"Error obteniendo última fecha: {e}")
            return None
    
    def close(self):
        """Cerrar la sesión HTTP."""
        self.session.close()
        logger.info("Sesión de API cerrada")


if __name__ == "__main__":
    """Ejemplo de uso del cliente de API."""
    
    # Crear cliente
    client = DatosAbiertosClient()
    
    print("=" * 70)
    print("PRUEBA DE CLIENTE DE API")
    print("=" * 70)
    
    # Probar extracción de homicidios (solo 5 registros)
    print("\n📊 Extrayendo 5 registros de homicidios...")
    homicidios = client.fetch_homicidios(limit=5)
    print(f"✅ Extraídos: {len(homicidios)} registros")
    if homicidios:
        print(f"   Primer registro: {homicidios[0].get('fecha_hecho', 'N/A')}")
    
    # Probar extracción de departamentos
    print("\n🗺️  Extrayendo departamentos...")
    departamentos = client.fetch_divipola_departamentos()
    print(f"✅ Extraídos: {len(departamentos)} departamentos")
    
    # Probar extracción de municipios
    print("\n🏘️  Extrayendo municipios...")
    municipios = client.fetch_divipola_municipios()
    print(f"✅ Extraídos: {len(municipios)} municipios")
    
    # Obtener última fecha
    print("\n📅 Obteniendo última fecha...")
    ultima_fecha = client.get_latest_fecha_hecho()
    print(f"✅ Última fecha: {ultima_fecha}")
    
    # Cerrar cliente
    client.close()
    
    print("\n" + "=" * 70)
