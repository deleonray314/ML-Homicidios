"""
Módulo de logging estructurado para ML-Homicidios.

Proporciona logging con formato JSON, rotación de archivos y configuración
basada en settings.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from src.config.settings import settings


class JSONFormatter(logging.Formatter):
    """Formatter para logs en formato JSON."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Formatear log record como JSON."""
        import json
        from datetime import datetime
        
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Agregar información de excepción si existe
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Agregar campos extra si existen
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Formatter para logs en formato texto legible."""
    
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


def setup_logger(
    name: str,
    level: Optional[str] = None,
    log_file: Optional[Path] = None,
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    Configurar y retornar un logger.
    
    Args:
        name: Nombre del logger
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Ruta del archivo de log (None para usar settings)
        log_format: Formato de log ('json' o 'text', None para usar settings)
    
    Returns:
        Logger configurado
    """
    # Usar valores de settings si no se especifican
    level = level or settings.log_level
    log_file = log_file or settings.log_file
    log_format = log_format or settings.log_format
    
    # Crear logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Evitar duplicar handlers si el logger ya existe
    if logger.handlers:
        return logger
    
    # Seleccionar formatter
    if log_format.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    # Handler para consola (siempre en formato texto para legibilidad)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(TextFormatter())
    logger.addHandler(console_handler)
    
    # Handler para archivo con rotación
    if log_file:
        # Asegurar que el directorio existe
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtener un logger ya configurado o crear uno nuevo.
    
    Args:
        name: Nombre del logger
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Si no tiene handlers, configurarlo
    if not logger.handlers:
        return setup_logger(name)
    
    return logger


# Logger por defecto para el módulo
logger = get_logger(__name__)


if __name__ == "__main__":
    """Ejemplo de uso del logger."""
    
    # Crear logger de prueba
    test_logger = setup_logger("test_logger", level="DEBUG")
    
    # Probar diferentes niveles
    test_logger.debug("Mensaje de debug")
    test_logger.info("Mensaje informativo")
    test_logger.warning("Mensaje de advertencia")
    test_logger.error("Mensaje de error")
    
    # Probar con excepción
    try:
        1 / 0
    except ZeroDivisionError:
        test_logger.exception("Error capturado")
    
    print(f"\n✅ Logs guardados en: {settings.log_file}")
