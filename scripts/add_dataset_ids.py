#!/usr/bin/env python
"""Agregar los dataset IDs al archivo .env"""

import sys
from pathlib import Path

env_file = Path(__file__).parent.parent / ".env"

# Dataset IDs correctos (ya probados anteriormente)
dataset_ids = {
    "DATOS_ABIERTOS_HOMICIDIOS_ID": "2p6v-dj4w",
    "DATOS_ABIERTOS_DIVIPOLA_DEPARTAMENTOS_ID": "gdxc-w37w",
    "DATOS_ABIERTOS_DIVIPOLA_MUNICIPIOS_ID": "xdk5-pm3f",
}

print("Agregando dataset IDs al .env...")

# Leer archivo
with open(env_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Buscar y actualizar
updated_lines = []
found_keys = set()

for line in lines:
    if "=" in line and not line.strip().startswith("#"):
        key = line.split("=")[0].strip()
        if key in dataset_ids:
            updated_lines.append(f"{key}={dataset_ids[key]}\n")
            found_keys.add(key)
            print(f"✅ {key}={dataset_ids[key]}")
        else:
            updated_lines.append(line)
    else:
        updated_lines.append(line)

# Agregar los que faltan
for key, value in dataset_ids.items():
    if key not in found_keys:
        updated_lines.append(f"\n{key}={value}\n")
        print(f"➕ {key}={value}")

# Escribir
with open(env_file, "w", encoding="utf-8") as f:
    f.writelines(updated_lines)

print("\n✅ Dataset IDs configurados")
