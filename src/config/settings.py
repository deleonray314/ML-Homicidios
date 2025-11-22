"""
Configuración centralizada del proyecto ML-Homicidios.

Este módulo usa Pydantic Settings para:
- Leer variables de entorno desde .env
- Validar configuración automáticamente
- Proporcionar valores por defecto
- Type hints para mejor desarrollo
"""

from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración principal del proyecto."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ========================================================================
    # API Datos Abiertos Colombia
    # ========================================================================
    
    # Dataset de Homicidios
    homicidios_id: str = Field(
        default="",
        validation_alias="DATOS_ABIERTOS_HOMICIDIOS_ID",
        description="ID del dataset de homicidios en Datos Abiertos"
    )
    
    # Dataset DIVIPOLA Departamentos
    departamentos_id: str = Field(
        default="",
        validation_alias="DATOS_ABIERTOS_DIVIPOLA_DEPARTAMENTOS_ID",
        description="ID del dataset DIVIPOLA de departamentos"
    )
    
    # Dataset DIVIPOLA Municipios
    municipios_id: str = Field(
        default="",
        validation_alias="DATOS_ABIERTOS_DIVIPOLA_MUNICIPIOS_ID",
        description="ID del dataset DIVIPOLA de municipios"
    )
    
    base_url: str = Field(
        default="https://www.datos.gov.co/resource/",
        validation_alias="DATOS_ABIERTOS_BASE_URL",
        description="URL base de la API de Datos Abiertos"
    )
    
    api_key: Optional[str] = Field(
        default=None,
        validation_alias="DATOS_ABIERTOS_API_KEY",
        description="API key (opcional para API pública)"
    )

    # ========================================================================
    # Database Configuration
    # ========================================================================
    
    db_type: str = Field(
        default="sqlite",
        description="Tipo de base de datos: sqlite, postgresql, mysql"
    )
    
    db_host: str = Field(default="localhost")
    db_port: int = Field(default=5432)
    db_name: str = Field(default="homicidios_db")
    db_user: str = Field(default="")
    db_password: str = Field(default="")
    db_path: Path = Field(
        default=Path("./data/homicidios.db"),
        description="Ruta para SQLite"
    )

    # ========================================================================
    # Data Paths
    # ========================================================================
    
    # Data Lake (datos crudos con transformaciones mínimas)
    data_raw_path: Path = Field(
        default=Path("./data/raw"),
        description="Data Lake - Datos crudos en Parquet"
    )
    
    # Data Warehouse (modelo estrella)
    data_processed_path: Path = Field(
        default=Path("./data/processed"),
        description="Data Warehouse - Modelo estrella"
    )
    
    # Modelos entrenados
    models_path: Path = Field(default=Path("./data/models"))
    
    @field_validator("data_raw_path", "data_processed_path", "models_path")
    @classmethod
    def create_directories(cls, v: Path) -> Path:
        """Crear directorios si no existen."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    # ========================================================================
    # Model Configuration
    # ========================================================================
    
    default_model: str = Field(
        default="xgboost",
        description="Modelo por defecto: xgboost, lightgbm, random_forest"
    )
    
    model_n_estimators: int = Field(default=100)
    model_max_depth: int = Field(default=6)
    model_learning_rate: float = Field(default=0.1)

    # ========================================================================
    # Logging
    # ========================================================================
    
    log_level: str = Field(
        default="INFO",
        description="Nivel de logging: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    
    log_file: Path = Field(default=Path("./logs/ml_homicidios.log"))
    log_format: str = Field(
        default="json",
        description="Formato de logs: json, text"
    )
    
    @field_validator("log_file")
    @classmethod
    def create_log_directory(cls, v: Path) -> Path:
        """Crear directorio de logs si no existe."""
        v.parent.mkdir(parents=True, exist_ok=True)
        return v

    # ========================================================================
    # Data Lake Configuration
    # ========================================================================
    
    # Estrategia de carga para Homicidios
    initial_load_completed: bool = Field(
        default=False,
        description="Si ya se hizo la carga inicial completa de homicidios"
    )
    
    # Estrategia de carga para DIVIPOLA (una sola vez)
    divipola_departamentos_loaded: bool = Field(
        default=False,
        description="Si ya se cargó DIVIPOLA Departamentos (carga única)"
    )
    
    divipola_municipios_loaded: bool = Field(
        default=False,
        description="Si ya se cargó DIVIPOLA Municipios (carga única)"
    )
    
    # Campo para detectar registros nuevos en cargas incrementales
    incremental_load_field: str = Field(
        default="fecha",
        description="Campo para detectar nuevos registros de homicidios (fecha, id, etc.)"
    )
    
    # Formato de almacenamiento en Data Lake
    data_lake_format: str = Field(
        default="parquet",
        description="Formato de archivos en Data Lake: parquet, csv"
    )
    
    # ========================================================================
    # Data Warehouse - Star Schema Configuration
    # ========================================================================
    
    # Tablas del modelo estrella
    fact_table_name: str = Field(
        default="fact_homicidios",
        description="Nombre de la tabla de hechos"
    )
    
    dim_fecha_table: str = Field(default="dim_fecha")
    dim_ubicacion_table: str = Field(default="dim_ubicacion")
    dim_victima_table: str = Field(default="dim_victima")
    dim_arma_table: str = Field(default="dim_arma")
    
    # ========================================================================
    # Cron Job Configuration
    # ========================================================================
    
    # Carga incremental: Cada VIERNES a las 2 AM
    data_extraction_schedule: str = Field(
        default="0 2 * * 5",
        description="Cron schedule para carga incremental (viernes)"
    )
    
    model_training_schedule: str = Field(
        default="0 3 * * 0",
        description="Cron schedule para reentrenamiento de modelos"
    )

    # ========================================================================
    # Streamlit Configuration
    # ========================================================================
    
    streamlit_server_port: int = Field(default=8501)
    streamlit_server_address: str = Field(default="localhost")

    # ========================================================================
    # MLflow (Opcional)
    # ========================================================================
    
    mlflow_tracking_uri: str = Field(default="./mlruns")
    mlflow_experiment_name: str = Field(default="homicidios-prediction")

    # ========================================================================
    # Feature Engineering
    # ========================================================================
    
    lag_days: str = Field(
        default="7,14,30,90",
        description="Días para features de lag (separados por comas)"
    )
    
    rolling_window: int = Field(
        default=30,
        description="Ventana para rolling averages (días)"
    )
    
    def get_lag_days_list(self) -> List[int]:
        """Convertir lag_days string a lista de enteros."""
        return [int(x.strip()) for x in self.lag_days.split(",")]

    # ========================================================================
    # Environment
    # ========================================================================
    
    environment: str = Field(
        default="development",
        description="Ambiente: development, production"
    )
    
    debug: bool = Field(default=True)

    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def get_database_url(self) -> str:
        """Construir URL de conexión a base de datos."""
        if self.db_type == "sqlite":
            return f"sqlite:///{self.db_path}"
        elif self.db_type == "postgresql":
            return (
                f"postgresql://{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )
        elif self.db_type == "mysql":
            return (
                f"mysql+mysqlconnector://{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )
        else:
            raise ValueError(f"Tipo de base de datos no soportado: {self.db_type}")
    
    def get_api_endpoint(self, dataset_type: str) -> str:
        """
        Construir endpoint de API para un dataset específico.
        
        Args:
            dataset_type: Tipo de dataset ('homicidios', 'departamentos', 'municipios')
        
        Returns:
            URL completa del endpoint
        """
        dataset_ids = {
            "homicidios": self.homicidios_id,
            "departamentos": self.departamentos_id,
            "municipios": self.municipios_id,
        }
        
        dataset_id = dataset_ids.get(dataset_type)
        if not dataset_id:
            raise ValueError(
                f"Dataset ID no configurado para: {dataset_type}. "
                f"Configura la variable de entorno correspondiente en .env"
            )
        
        return f"{self.base_url}{dataset_id}.json"
    
    def is_production(self) -> bool:
        """Verificar si estamos en ambiente de producción."""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Verificar si estamos en ambiente de desarrollo."""
        return self.environment.lower() == "development"


# ============================================================================
# Singleton de configuración
# ============================================================================

# Instancia global de configuración (se carga una sola vez)
settings = Settings()


# ============================================================================
# Ejemplo de uso
# ============================================================================

if __name__ == "__main__":
    """Ejemplo de uso y validación de configuración."""
    
    print("=" * 70)
    print("CONFIGURACIÓN ML-HOMICIDIOS")
    print("=" * 70)
    
    print(f"\n📊 Datasets:")
    print(f"  - Homicidios ID: {settings.homicidios_id or 'NO CONFIGURADO'}")
    print(f"  - Departamentos ID: {settings.departamentos_id or 'NO CONFIGURADO'}")
    print(f"  - Municipios ID: {settings.municipios_id or 'NO CONFIGURADO'}")
    print(f"  - Base URL: {settings.base_url}")
    
    print(f"\n💾 Base de Datos:")
    print(f"  - Tipo: {settings.db_type}")
    print(f"  - URL: {settings.get_database_url()}")
    
    print(f"\n📁 Rutas:")
    print(f"  - Raw: {settings.data_raw_path}")
    print(f"  - Processed: {settings.data_processed_path}")
    print(f"  - Models: {settings.models_path}")
    
    print(f"\n🤖 Modelo:")
    print(f"  - Tipo: {settings.default_model}")
    print(f"  - N Estimators: {settings.model_n_estimators}")
    print(f"  - Max Depth: {settings.model_max_depth}")
    
    print(f"\n📝 Logging:")
    print(f"  - Level: {settings.log_level}")
    print(f"  - File: {settings.log_file}")
    
    print(f"\n🌍 Ambiente:")
    print(f"  - Environment: {settings.environment}")
    print(f"  - Debug: {settings.debug}")
    print(f"  - Is Production: {settings.is_production()}")
    
    print("\n" + "=" * 70)
    
    # Ejemplo de obtener endpoints
    try:
        print("\n🔗 Endpoints de API:")
        for dataset_type in ["homicidios", "departamentos", "municipios"]:
            try:
                endpoint = settings.get_api_endpoint(dataset_type)
                print(f"  - {dataset_type.capitalize()}: {endpoint}")
            except ValueError as e:
                print(f"  - {dataset_type.capitalize()}: ⚠️  {e}")
    except Exception as e:
        print(f"  Error: {e}")
