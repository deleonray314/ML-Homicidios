# 📚 Manual Completo - Proyecto ML-Homicidios

## 🎯 Descripción del Proyecto

Sistema completo de análisis y predicción de homicidios en Colombia, implementando una arquitectura de datos moderna con Data Lake, Data Warehouse (modelo estrella), y pipelines ETL automatizados.

---

## 📖 Índice de Documentación

### **🗄️ Data Lake**

| Documento | Descripción |
|-----------|-------------|
| [DL_ETL_Quickstart.md](DL_ETL_Quickstart.md) | Guía rápida para ejecutar el ETL del Data Lake |
| [DL_Cron_Usage.md](DL_Cron_Usage.md) | Uso del servicio ETL con cron automático |
| [DL_Cron_Checklist.md](DL_Cron_Checklist.md) | Checklist de implementación y verificación |
| [DL_Loading_Strategy.md](DL_Loading_Strategy.md) | Estrategia de carga inicial e incremental |
| [DL_Migracion_Integer.md](DL_Migracion_Integer.md) | Migración de códigos DIVIPOLA a INTEGER |

### **🏢 Data Warehouse**

| Documento | Descripción |
|-----------|-------------|
| [DWH_Modelo_Estrella.md](DWH_Modelo_Estrella.md) | Diagrama ER del modelo estrella |
| [DWH_Schema_Design.md](DWH_Schema_Design.md) | Diseño detallado del schema |
| [DWH_ETL_Quickstart.md](DWH_ETL_Quickstart.md) | Guía rápida del ETL DWH |

### **🐳 Docker & Infraestructura**

| Documento | Ubicación | Descripción |
|-----------|-----------|-------------|
| [QUICKSTART.md](../docker/QUICKSTART.md) | `docker/` | Inicio rápido con Docker |
| [ADMINER_GUIDE.md](../docker/ADMINER_GUIDE.md) | `docker/` | Guía de uso de Adminer |
| [NETWORK_ACCESS.md](../docker/NETWORK_ACCESS.md) | `docker/` | Configuración de red |

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    FUENTE DE DATOS                          │
│              API Datos Abiertos Colombia                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ ETL Semanal (Viernes 23:00)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     DATA LAKE                               │
│              PostgreSQL - Datos Raw                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │ raw_homicidios                                     │    │
│  │ raw_divipola_departamentos                         │    │
│  │ raw_divipola_municipios                            │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ ETL Transformación (Sábado 01:00)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  DATA WAREHOUSE                             │
│           PostgreSQL - Modelo Estrella                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Dimensiones:                                       │    │
│  │  - dim_fecha (8,340 registros)                     │    │
│  │  - dim_departamento (33 registros)                 │    │
│  │  - dim_municipio (1,121 registros)                 │    │
│  │  - dim_sexo (6 registros)                          │    │
│  │                                                     │    │
│  │ Hechos:                                            │    │
│  │  - fact_homicidios (332,131 registros)             │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Análisis & ML
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              CAPA DE ANÁLISIS (Futuro)                      │
│  - Dashboards (Streamlit/PowerBI)                          │
│  - Modelos ML (XGBoost, LightGBM)                          │
│  - APIs de Predicción                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Inicio Rápido

### **1. Levantar Infraestructura**

```bash
# Clonar repositorio
git clone <repo-url>
cd ML-Homicidios

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de API

# Levantar servicios Docker
docker-compose up -d

# Verificar que todo esté corriendo
docker ps
```

### **2. Carga Inicial de Datos**

```bash
# Data Lake - Carga inicial
docker exec ml-homicidios-etl-cron python scripts/load_datalake.py --initial

# Data Warehouse - Carga inicial
docker exec ml-homicidios-etl-cron python scripts/load_datawarehouse.py --initial
```

### **3. Verificar Datos**

```bash
# Acceder a Adminer
# URL: http://localhost:8080

# Data Lake
# Servidor: datalake | Usuario: datalake_user | Password: datalake_password_2024

# Data Warehouse
# Servidor: datawarehouse | Usuario: dw_user | Password: dw_password_2024
```

---

## 📊 Datos Disponibles

### **Data Lake (Raw)**
- **Homicidios**: ~332,000 registros (2003-2025)
- **Departamentos**: 33 departamentos
- **Municipios**: 1,121 municipios

### **Data Warehouse (Transformado)**
- **Dimensión Temporal**: 8,340 fechas
- **Dimensión Geográfica**: 33 departamentos + 1,121 municipios
- **Dimensión Demográfica**: 6 categorías de sexo
- **Tabla de Hechos**: 332,131 homicidios

---

## 🤖 Automatización

### **Cron Jobs Configurados**

| Proceso | Frecuencia | Hora | Log |
|---------|------------|------|-----|
| Carga Data Lake | Viernes | 23:00 | `/app/logs/cron.log` |
| Carga Data Warehouse | Sábado | 01:00 | `/app/logs/cron_dwh.log` |
| Catch-up Data Lake | Diario | 08:00 | `/app/logs/catchup.log` |
| Catch-up DWH | Diario | 09:00 | `/app/logs/catchup_dwh.log` |
| Health Check | Diario | 02:00 | `/app/logs/health.log` |

### **Monitoreo**

```bash
# Ver logs en tiempo real
docker exec ml-homicidios-etl-cron tail -f /app/logs/cron.log
docker exec ml-homicidios-etl-cron tail -f /app/logs/cron_dwh.log

# Ver estado de contenedores
docker ps

# Ver logs de contenedor específico
docker logs ml-homicidios-etl-cron --tail 50
```

---

## 🔧 Comandos Útiles

### **Data Lake**

```bash
# Carga inicial
docker exec ml-homicidios-etl-cron python scripts/load_datalake.py --initial

# Carga incremental
docker exec ml-homicidios-etl-cron python scripts/load_datalake.py --incremental

# Verificar catch-up
docker exec ml-homicidios-etl-cron python scripts/catchup_check.py

# Health check
docker exec ml-homicidios-etl-cron python scripts/health_check.py
```

### **Data Warehouse**

```bash
# Carga inicial
docker exec ml-homicidios-etl-cron python scripts/load_datawarehouse.py --initial

# Carga incremental
docker exec ml-homicidios-etl-cron python scripts/load_datawarehouse.py --incremental

# Verificar catch-up
docker exec ml-homicidios-etl-cron python scripts/catchup_check_dwh.py
```

### **Base de Datos**

```bash
# Conectar a Data Lake
docker exec -it ml-homicidios-datalake psql -U datalake_user -d homicidios_datalake

# Conectar a Data Warehouse
docker exec -it ml-homicidios-datawarehouse psql -U dw_user -d homicidios_dw

# Contar registros
docker exec ml-homicidios-datalake psql -U datalake_user -d homicidios_datalake -c "SELECT COUNT(*) FROM raw_homicidios;"
docker exec ml-homicidios-datawarehouse psql -U dw_user -d homicidios_dw -c "SELECT COUNT(*) FROM fact_homicidios;"
```

---

## 📈 Vistas Analíticas (DWH)

El Data Warehouse incluye vistas pre-calculadas para análisis:

```sql
-- Homicidios por departamento
SELECT * FROM v_homicidios_por_departamento LIMIT 10;

-- Homicidios por municipio
SELECT * FROM v_homicidios_por_municipio LIMIT 10;

-- Homicidios por sexo
SELECT * FROM v_homicidios_por_sexo;

-- Homicidios por mes
SELECT * FROM v_homicidios_por_mes ORDER BY año DESC, mes DESC LIMIT 12;
```

---

## 🛠️ Mantenimiento

### **Reiniciar Servicios**

```bash
# Reiniciar todos los servicios
docker-compose restart

# Reiniciar servicio específico
docker-compose restart etl-cron
docker-compose restart datalake
docker-compose restart datawarehouse
```

### **Limpiar y Recrear**

```bash
# Detener servicios
docker-compose down

# Eliminar volúmenes (CUIDADO: Borra todos los datos)
docker volume rm ml-homicidios-datalake-data
docker volume rm ml-homicidios-datawarehouse-data

# Recrear desde cero
docker-compose up -d

# Esperar a que estén healthy
docker ps

# Cargar datos nuevamente
docker exec ml-homicidios-etl-cron python scripts/load_datalake.py --initial
docker exec ml-homicidios-etl-cron python scripts/load_datawarehouse.py --initial
```

---

## 📝 Estructura del Proyecto

```
ML-Homicidios/
├── docker/                      # Configuración Docker
│   ├── Dockerfile.etl          # Imagen del servicio ETL
│   ├── entrypoint-cron.sh      # Script de inicio
│   ├── crontab                 # Cron jobs
│   └── init-scripts/           # Scripts de inicialización DB
│       ├── 01-create-datalake-schema.sql
│       └── 02-create-datawarehouse-schema.sql
├── src/                        # Código fuente
│   ├── config/                 # Configuración
│   ├── data_ingestion/         # ETL Data Lake
│   └── data_warehouse/         # ETL Data Warehouse
├── scripts/                    # Scripts de ejecución
│   ├── load_datalake.py
│   ├── load_datawarehouse.py
│   ├── catchup_check.py
│   ├── catchup_check_dwh.py
│   └── health_check.py
├── docs/                       # Documentación
│   ├── README.md              # Este archivo
│   ├── DL_*.md                # Docs Data Lake
│   └── DWH_*.md               # Docs Data Warehouse
├── docker-compose.yml          # Orquestación de servicios
├── .env.example               # Template de variables
└── requirements.txt           # Dependencias Python
```

---

## 🔐 Seguridad

- ✅ Credenciales en `.env` (nunca en Git)
- ✅ `.env` en `.gitignore`
- ✅ Contraseñas fuertes por defecto
- ✅ Red Docker aislada
- ✅ Puertos expuestos solo los necesarios

---

## 🐛 Troubleshooting

### **Contenedor ETL reiniciando**

```bash
# Ver logs
docker logs ml-homicidios-etl-cron --tail 100

# Verificar conexiones
docker exec ml-homicidios-etl-cron python -c "from src.data_ingestion.db_connection import DatabaseConnection; db = DatabaseConnection(); print('OK' if db.test_connection() else 'FAIL')"
```

### **No hay datos en DWH**

```bash
# Verificar Data Lake
docker exec ml-homicidios-datalake psql -U datalake_user -d homicidios_datalake -c "SELECT COUNT(*) FROM raw_homicidios;"

# Ejecutar carga inicial DWH
docker exec ml-homicidios-etl-cron python scripts/load_datawarehouse.py --initial
```

### **Cron jobs no ejecutan**

```bash
# Verificar crontab
docker exec ml-homicidios-etl-cron crontab -l

# Ver logs de cron
docker exec ml-homicidios-etl-cron tail -f /app/logs/cron.log
```

---

## 📞 Soporte

Para más información, consulta la documentación específica en la carpeta `docs/`:
- **Data Lake**: Archivos con prefijo `DL_`
- **Data Warehouse**: Archivos con prefijo `DWH_`
- **Docker**: Carpeta `docker/`

---

## ✅ Checklist de Implementación

- [x] Docker Compose configurado
- [x] Data Lake schema creado
- [x] Data Warehouse schema creado
- [x] ETL Data Lake implementado
- [x] ETL Data Warehouse implementado
- [x] Cron jobs configurados
- [x] Catch-up automático implementado
- [x] Health checks configurados
- [x] Documentación completa
- [x] Vistas analíticas creadas

---

¡El sistema está listo para análisis y Machine Learning! 🚀
