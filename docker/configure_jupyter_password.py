#!/usr/bin/env python3
"""
Script para configurar contraseña de Jupyter Lab
"""
from jupyter_server.auth import passwd
import json
import os

# Contraseña definida
PASSWORD = "ML-Homicidios2003!"

# Generar hash
password_hash = passwd(PASSWORD)

# Configuración
config = {
    'ServerApp': {
        'password': password_hash,
        'token': '',
        'password_required': True
    }
}

# Crear directorio si no existe
config_dir = os.path.expanduser('~/.jupyter')
os.makedirs(config_dir, exist_ok=True)

# Guardar configuración
config_file = os.path.join(config_dir, 'jupyter_server_config.json')
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print(f"✅ Configuración guardada en: {config_file}")
print(f"🔑 Contraseña configurada: {PASSWORD}")
