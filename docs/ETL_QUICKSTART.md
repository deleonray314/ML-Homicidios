# 🚀 Guía Rápida: Ejecutar ETL del Data Lake

## ✅ Pasos Completados

1. ✅ Docker corriendo (Data Lake, Data Warehouse, Adminer)
2. ✅ Esquemas de base de datos creados
3. ✅ Código ETL implementado:
   - `src/utils/logger.py` - Logging estructurado
   - `src/data_ingestion/api_client.py` - Cliente de API
   - `src/data_ingestion/db_connection.py` - Conexión a PostgreSQL
   - `src/data_ingestion/data_lake_loader.py` - Cargador de datos
   - `scripts/load_datalake.py` - Script principal

## 🔧 Problema Actual

El puerto 5433 no está expuesto. Necesitas reiniciar Docker.

## 🎯 Solución Rápida

```bash
# 1. Detener Docker
docker-compose down

# 2. Iniciar Docker (con puerto 5433 expuesto)
docker-compose up -d

# 3. Esperar 10 segundos para que inicie

# 4. Probar carga de departamentos
python scripts/load_datalake.py --dataset departamentos
```

## 📊 Comandos Disponibles

### Carga Inicial Completa
```bash
python scripts/load_datalake.py --initial
```

### Carga Incremental
```bash
python scripts/load_datalake.py --incremental
```

### Cargar Dataset Específico
```bash
# Departamentos (33 registros)
python scripts/load_datalake.py --dataset departamentos

# Municipios (~1100 registros)
python scripts/load_datalake.py --dataset municipios

# Homicidios (todos los registros históricos)
python scripts/load_datalake.py --dataset homicidios --initial
```

## 🔍 Verificar Datos en Adminer

1. Abre: http://localhost:8080
2. Conecta:
   - Sistema: PostgreSQL
   - Servidor: `datalake`
   - Usuario: `datalake_user`
   - Contraseña: `datalake_password_2024`
   - Base de datos: `homicidios_datalake`
3. Explora las tablas:
   - `raw_homicidios`
   - `raw_divipola_departamentos`
   - `raw_divipola_municipios`
   - `data_load_log`

## ⚠️ Troubleshooting

**Error: Connection refused**
- Solución: Reinicia Docker con `docker-compose down && docker-compose up -d`

**Error: No module named 'src'**
- Solución: Ejecuta desde la raíz del proyecto, no desde `src/`

**Error: API timeout**
- Solución: Verifica tu conexión a internet
- La API de Datos Abiertos puede estar lenta

## 📝 Próximos Pasos

Después de cargar los datos:
1. Verificar en Adminer que los datos se cargaron
2. Implementar ETL del Data Warehouse (transformación al modelo estrella)
3. Crear dashboards en Streamlit
