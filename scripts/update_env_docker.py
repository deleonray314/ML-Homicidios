#!/usr/bin/env python
"""
Script para actualizar el archivo .env con las credenciales correctas de Docker.
"""

import sys
from pathlib import Path

# Ruta al archivo .env
env_file = Path(__file__).parent.parent / ".env"

# Configuración para Docker
docker_config = {
    "DB_TYPE": "postgresql",
    "DB_HOST": "localhost",
    "DB_PORT": "5433",
    "DB_NAME": "homicidios_datalake",
    "DB_USER": "datalake_user",
    "DB_PASSWORD": "datalake_password_2024",
}

print("=" * 70)
print("ACTUALIZAR .ENV PARA DOCKER")
print("=" * 70)

if not env_file.exists():
    print(f"\n❌ Archivo .env no encontrado en: {env_file}")
    print("   Creando desde .env.example...")
    
    env_example = env_file.parent / ".env.example"
    if env_example.exists():
        import shutil
        shutil.copy(env_example, env_file)
        print(f"✅ Archivo .env creado")
    else:
        print(f"❌ Tampoco existe .env.example")
        sys.exit(1)

# Leer archivo actual
with open(env_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Actualizar líneas
updated_lines = []
updated_keys = set()

for line in lines:
    # Saltar líneas vacías y comentarios
    if not line.strip() or line.strip().startswith("#"):
        updated_lines.append(line)
        continue
    
    # Buscar clave=valor
    if "=" in line:
        key = line.split("=")[0].strip()
        
        if key in docker_config:
            # Actualizar con nuevo valor
            updated_lines.append(f"{key}={docker_config[key]}\n")
            updated_keys.add(key)
            print(f"✅ Actualizado: {key}={docker_config[key]}")
        else:
            # Mantener línea original
            updated_lines.append(line)
    else:
        updated_lines.append(line)

# Agregar claves faltantes
for key, value in docker_config.items():
    if key not in updated_keys:
        updated_lines.append(f"\n{key}={value}\n")
        print(f"➕ Agregado: {key}={value}")

# Escribir archivo actualizado
with open(env_file, "w", encoding="utf-8") as f:
    f.writelines(updated_lines)

print("\n" + "=" * 70)
print("✅ Archivo .env actualizado correctamente")
print("=" * 70)
print("\nConfiguración de base de datos:")
for key, value in docker_config.items():
    print(f"  {key}: {value}")
print("\n" + "=" * 70)
