# 📊 Jupyter Lab - Guía de Uso

Este directorio contiene notebooks de Jupyter para análisis exploratorio de datos (EDA) del proyecto ML-Homicidios.

## 🚀 Acceso a Jupyter Lab

### Iniciar el servicio

```bash
# Desde la raíz del proyecto
docker compose up -d jupyter
```

### Opción 1: Acceder desde el Navegador

1. Abre tu navegador en: **http://localhost:8888/lab**
2. Ingresa la contraseña: `ML-Homicidios2003!`
3. ¡Listo! Ya puedes trabajar en Jupyter Lab desde el navegador

### Opción 2: Conectar desde VS Code (Recomendado)

#### **Método 1: Autenticación directa (puede requerir navegador primero)**

1. **Abre tu notebook** (ej: `EDA.ipynb`) en VS Code
2. **Haz clic en "Select Kernel"** (esquina superior derecha)
3. **Selecciona "Existing Jupyter Server..."**
4. **Ingresa la URL**: `http://localhost:8888/lab`
5. **Ingresa la contraseña**: `ML-Homicidios2003!`
6. **Selecciona el kernel Python** que aparezca (Python 3.12)

> **Nota:** Si VS Code no acepta la contraseña directamente, usa el Método 2.

#### **Método 2: Conexión después de autenticarte en navegador (más confiable)**

1. **Primero, abre Jupyter en el navegador**: http://localhost:8888/lab
2. **Ingresa la contraseña**: `ML-Homicidios2003!`
3. **Copia la URL completa** de la barra de direcciones del navegador
4. **En VS Code**, haz clic en "Select Kernel"
5. **Selecciona "Existing Jupyter Server..."**
6. **Pega la URL completa** que copiaste del navegador
7. **Selecciona el kernel Python 3.12**

#### **Verificar Conexión**

Ejecuta esta celda en tu notebook:

```python
import sys
print(f"Python: {sys.version}")
print(f"Ejecutando en: {sys.prefix}")
```

Deberías ver que estás usando Python 3.12 desde `/usr/local`

### Detener el servicio

```bash
docker compose stop jupyter
```

---

## 🔌 Conexión a las Bases de Datos

Desde los notebooks, puedes conectarte a las bases de datos usando los **nombres de host internos de Docker**:

### Data Warehouse (DWH)

```python
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv('/app/.env')

# Configuración para conexión DENTRO de Docker
DW_USER = os.getenv('DW_USER')
DW_PASSWORD = os.getenv('DW_PASSWORD')
DW_HOST = 'datawarehouse'  # ← Nombre del servicio Docker
DW_PORT = '5432'           # ← Puerto interno (no 5434)
DW_DB = os.getenv('DW_DB')

# Crear conexión
connection_string = f"postgresql://{DW_USER}:{DW_PASSWORD}@{DW_HOST}:{DW_PORT}/{DW_DB}"
engine = create_engine(connection_string)

# Ejecutar consulta
df = pd.read_sql("SELECT * FROM fact_homicidios LIMIT 10;", engine)
print(df)
```

### Data Lake

```python
# Configuración para Data Lake
DL_USER = os.getenv('DATALAKE_USER')
DL_PASSWORD = os.getenv('DATALAKE_PASSWORD')
DL_HOST = 'datalake'  # ← Nombre del servicio Docker
DL_PORT = '5432'      # ← Puerto interno
DL_DB = os.getenv('DATALAKE_DB')

connection_string = f"postgresql://{DL_USER}:{DL_PASSWORD}@{DL_HOST}:{DL_PORT}/{DL_DB}"
engine_dl = create_engine(connection_string)
```

---

## 🔑 Credenciales de Acceso

### Jupyter Lab

- **URL**: http://localhost:8888/lab
- **Contraseña**: `ML-Homicidios2003!`

### Bases de Datos

Las credenciales de las bases de datos se cargan automáticamente desde el archivo `.env` montado en `/app/.env`.

**Variables disponibles:**

- `DW_USER`, `DW_PASSWORD`, `DW_DB` (Data Warehouse)
- `DATALAKE_USER`, `DATALAKE_PASSWORD`, `DATALAKE_DB` (Data Lake)

**Importante:**

- Usa `host='datawarehouse'` y `port=5432` (NO `localhost:5434`)
- Usa `host='datalake'` y `port=5432` (NO `localhost:5433`)

---

## 📂 Estructura de Notebooks

```
notebooks/
├── README.md              # Este archivo
├── EDA.ipynb             # Análisis exploratorio inicial
└── [otros notebooks]     # Tus análisis adicionales
```

---

## 💡 Tips

1. **Persistencia**: Los notebooks se guardan automáticamente en `./notebooks/` del proyecto
2. **Código fuente**: Puedes acceder al código en `/app/src/` y `/app/scripts/` (solo lectura)
3. **Librerías instaladas**: pandas, numpy, matplotlib, seaborn, plotly, sqlalchemy, psycopg2-binary
4. **Zona horaria**: Configurada a `America/Bogota`

---

## 🔍 Ejemplo de Consulta Exploratoria

```python
# Listar todas las tablas del DWH
query = """
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
"""
tables = pd.read_sql(query, engine)
print(tables)

# Ver estructura de una tabla
query = """
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'fact_homicidios'
ORDER BY ordinal_position;
"""
schema = pd.read_sql(query, engine)
print(schema)
```

---

## 🐛 Troubleshooting

**Error: "could not translate host name"**

- Asegúrate de usar `datawarehouse` o `datalake` como host (NO `localhost`)
- Verifica que los contenedores estén corriendo: `docker compose ps`

**Error: "No module named 'X'"**

- Las librerías están instaladas en el contenedor, no en tu entorno local
- Si necesitas una librería adicional, agrégala al `Dockerfile.jupyter`

**No puedo acceder a http://localhost:8888**

- Verifica que el contenedor esté corriendo: `docker compose ps`
- Revisa los logs: `docker compose logs jupyter`

**La contraseña no funciona en VS Code**

- **Solución recomendada**: Usa el Método 2 (autentícate primero en el navegador)
  1. Abre http://localhost:8888/lab en tu navegador
  2. Ingresa la contraseña: `ML-Homicidios2003!`
  3. Copia la URL completa del navegador
  4. Usa esa URL en VS Code para conectarte

**La contraseña no funciona en el navegador**

- Asegúrate de usar: `ML-Homicidios2003!` (con mayúsculas y signos exactos)
- Si cambiaste la contraseña, reinicia el contenedor: `docker compose restart jupyter`
- Verifica que el contenedor esté corriendo: `docker compose ps`
