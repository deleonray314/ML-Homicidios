"""
Script de diagnóstico para verificar la configuración del .env
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env
env_path = Path(".env")
if env_path.exists():
    load_dotenv(env_path)
    print("✅ Archivo .env encontrado y cargado\n")
else:
    print("❌ Archivo .env NO encontrado\n")
    exit(1)

print("=" * 70)
print("DIAGNÓSTICO DE CONFIGURACIÓN")
print("=" * 70)

# Variables esperadas
expected_vars = [
    "DATOS_ABIERTOS_HOMICIDIOS_ID",
    "DATOS_ABIERTOS_DIVIPOLA_DEPARTAMENTOS_ID",
    "DATOS_ABIERTOS_DIVIPOLA_MUNICIPIOS_ID",
    "DATOS_ABIERTOS_BASE_URL",
    "DATOS_ABIERTOS_API_KEY",
]

print("\n📋 Variables de Entorno Esperadas:\n")

for var in expected_vars:
    value = os.getenv(var)
    if value:
        # Ocultar parcialmente valores sensibles
        if len(value) > 10:
            display_value = f"{value[:4]}...{value[-4:]}"
        else:
            display_value = value
        print(f"  ✅ {var}: {display_value}")
    else:
        print(f"  ❌ {var}: NO CONFIGURADO")

print("\n" + "=" * 70)
print("\n🔍 Todas las variables que empiezan con 'DATOS_ABIERTOS':\n")

for key, value in os.environ.items():
    if key.startswith("DATOS_ABIERTOS"):
        if len(value) > 10:
            display_value = f"{value[:4]}...{value[-4:]}"
        else:
            display_value = value
        print(f"  {key}: {display_value}")

print("\n" + "=" * 70)

# Intentar cargar settings
print("\n🧪 Intentando cargar configuración con Pydantic...\n")

try:
    from src.config.settings import settings
    
    print("✅ Configuración cargada exitosamente\n")
    print(f"  - Homicidios ID: {settings.homicidios_id or 'VACÍO'}")
    print(f"  - Departamentos ID: {settings.departamentos_id or 'VACÍO'}")
    print(f"  - Municipios ID: {settings.municipios_id or 'VACÍO'}")
    print(f"  - Base URL: {settings.base_url}")
    
    # Probar endpoints
    print("\n🔗 Probando construcción de endpoints:\n")
    for dataset_type in ["homicidios", "departamentos", "municipios"]:
        try:
            endpoint = settings.get_api_endpoint(dataset_type)
            print(f"  ✅ {dataset_type}: {endpoint}")
        except ValueError as e:
            print(f"  ❌ {dataset_type}: {e}")
            
except Exception as e:
    print(f"❌ Error al cargar configuración: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
