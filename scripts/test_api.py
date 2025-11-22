"""
Script para probar conexión a la API de Datos Abiertos
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import requests
from src.config.settings import settings

print("=" * 70)
print("PRUEBA DE CONEXIÓN A API DE DATOS ABIERTOS")
print("=" * 70)

datasets = {
    "Homicidios": "homicidios",
    "DIVIPOLA Departamentos": "departamentos",
    "DIVIPOLA Municipios": "municipios"
}

for name, dataset_type in datasets.items():
    print(f"\n🔍 Probando: {name}")
    print("-" * 70)
    
    try:
        # Obtener endpoint
        endpoint = settings.get_api_endpoint(dataset_type)
        print(f"  Endpoint: {endpoint}")
        
        # Hacer request (solo 5 registros para prueba)
        test_url = f"{endpoint}?$limit=5"
        print(f"  Haciendo request...")
        response = requests.get(test_url, timeout=10)
        
        # Verificar respuesta
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Conexión exitosa!")
            print(f"  📊 Registros obtenidos: {len(data)}")
            
            if data:
                print(f"  📋 Primeros campos: {list(data[0].keys())[:8]}")
            else:
                print(f"  ⚠️  Dataset vacío (sin registros)")
        else:
            print(f"  ❌ Error HTTP {response.status_code}")
            print(f"  Respuesta: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print(f"  ❌ Timeout - La API tardó demasiado en responder")
    except requests.exceptions.ConnectionError:
        print(f"  ❌ Error de conexión - Verifica tu internet")
    except ValueError as e:
        print(f"  ❌ Error de configuración: {e}")
    except Exception as e:
        print(f"  ❌ Error inesperado: {type(e).__name__}: {e}")

print("\n" + "=" * 70)
print("✅ Prueba completada")
print("=" * 70)
