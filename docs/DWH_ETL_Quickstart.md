# 🚀 Guía Rápida: ETL Data Warehouse

## 📋 Resumen

El ETL del Data Warehouse transforma datos del Data Lake (raw) al Data Warehouse (modelo estrella) para análisis y ML.

---

## 🏗️ Arquitectura

```
Data Lake (Raw)          ETL Transform          Data Warehouse (Star Schema)
┌──────────────┐        ┌──────────────┐        ┌──────────────────────┐
│ raw_homicidios│───────▶│ Dimensiones  │───────▶│ dim_fecha            │
│ raw_divipola  │        │ + Hechos     │        │ dim_departamento     │
└──────────────┘        └──────────────┘        │ dim_municipio        │
                                                 │ dim_sexo             │
                                                 │ fact_homicidios      │
                                                 └──────────────────────┘
```

---

## 🎯 Carga Inicial (Primera Vez)

```bash
# 1. Asegurarse que Data Lake tiene datos
docker exec ml-homicidios-etl-cron python scripts/load_datalake.py --initial

# 2. Ejecutar carga inicial del DWH
docker exec ml-homicidios-etl-cron python scripts/load_datawarehouse.py --initial
```

**Esto carga:**
- ✅ `dim_departamento` (33 registros)
- ✅ `dim_municipio` (1,121 registros)
- ✅ `dim_sexo` (3 registros)
- ✅ `dim_fecha` (~7,000 fechas)
- ✅ `fact_homicidios` (~332,000 homicidios)

---

## 🔄 Carga Incremental (Automática)

### **Cron Jobs Configurados:**

| Tarea | Día | Hora | Descripción |
|-------|-----|------|-------------|
| **Data Lake → API** | Viernes | 23:00 | Extrae nuevos homicidios |
| **DWH ← Data Lake** | Sábado | 01:00 | Transforma a modelo estrella |
| **Catch-up Data Lake** | Diario | 08:00 | Verifica cargas perdidas |
| **Catch-up DWH** | Diario | 09:00 | Verifica cargas perdidas DWH |

### **Flujo Semanal:**
```
Viernes 23:00  → API → Data Lake (raw_homicidios)
Sábado  01:00  → Data Lake → DWH (fact_homicidios)
```

---

## 🧪 Pruebas Manuales

### **Ejecutar carga incremental manualmente:**

```bash
# DWH incremental
docker exec ml-homicidios-etl-cron python scripts/load_datawarehouse.py --incremental
```

### **Verificar catch-up DWH:**

```bash
docker exec ml-homicidios-etl-cron python scripts/catchup_check_dwh.py
```

### **Ver logs:**

```bash
# Logs del ETL DWH
docker exec ml-homicidios-etl-cron tail -f /app/logs/cron_dwh.log

# Logs de catch-up DWH
docker exec ml-homicidios-etl-cron tail -f /app/logs/catchup_dwh.log
```

---

## 📊 Verificar Datos en DWH

### **Conectar a Adminer:**
- URL: http://localhost:8080
- Sistema: PostgreSQL
- Servidor: `datawarehouse`
- Usuario: `dw_user`
- Contraseña: `dw_password_2024`
- Base de datos: `homicidios_dw`

### **Queries de Verificación:**

```sql
-- Contar registros en dimensiones
SELECT 'dim_fecha' as tabla, COUNT(*) as registros FROM dim_fecha
UNION ALL
SELECT 'dim_departamento', COUNT(*) FROM dim_departamento
UNION ALL
SELECT 'dim_municipio', COUNT(*) FROM dim_municipio
UNION ALL
SELECT 'dim_sexo', COUNT(*) FROM dim_sexo
UNION ALL
SELECT 'fact_homicidios', COUNT(*) FROM fact_homicidios;

-- Ver últimas cargas ETL
SELECT * FROM etl_log ORDER BY completed_at DESC LIMIT 5;

-- Homicidios por departamento
SELECT * FROM v_homicidios_por_departamento LIMIT 10;

-- Homicidios por mes
SELECT * FROM v_homicidios_por_mes ORDER BY año DESC, mes DESC LIMIT 12;
```

---

## 🔍 Monitoreo

### **Ver estado del ETL:**

```bash
# Ver todas las cargas ETL
docker exec ml-homicidios-datawarehouse psql -U dw_user -d homicidios_dw -c "SELECT process_name, records_processed, status, completed_at FROM etl_log ORDER BY completed_at DESC LIMIT 10;"
```

---

## 🛠️ Troubleshooting

### **Problema: No hay datos en DWH**

```bash
# Verificar que Data Lake tiene datos
docker exec ml-homicidios-datalake psql -U datalake_user -d homicidios_datalake -c "SELECT COUNT(*) FROM raw_homicidios;"

# Ejecutar carga inicial
docker exec ml-homicidios-etl-cron python scripts/load_datawarehouse.py --initial
```

### **Problema: Carga incremental no detecta nuevos datos**

```bash
# Ver última carga en DWH
docker exec ml-homicidios-datawarehouse psql -U dw_user -d homicidios_dw -c "SELECT MAX(loaded_at) FROM fact_homicidios;"

# Ver última carga en Data Lake
docker exec ml-homicidios-datalake psql -U datalake_user -d homicidios_datalake -c "SELECT MAX(loaded_at) FROM raw_homicidios;"
```

---

## 📁 Archivos Creados

```
src/data_warehouse/
├── __init__.py
├── dwh_connection.py          # Conexión al DWH
└── dwh_etl_loader.py          # Lógica ETL completa

scripts/
├── load_datawarehouse.py      # Script principal ETL
└── catchup_check_dwh.py       # Verificación de cargas perdidas

docker/
└── crontab                    # Cron jobs actualizados
```

---

## ✅ Checklist de Verificación

- [ ] Data Lake tiene datos (`raw_homicidios`, `raw_divipola_*`)
- [ ] Carga inicial DWH ejecutada
- [ ] Dimensiones pobladas (departamento, municipio, sexo, fecha)
- [ ] Tabla de hechos poblada (`fact_homicidios`)
- [ ] Cron jobs configurados
- [ ] Catch-up automático funciona
- [ ] Logs se generan correctamente

---

¡El ETL del Data Warehouse está listo! 🎉
