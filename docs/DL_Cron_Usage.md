# 🚀 Guía de Uso: Servicio ETL con Cron

## 📋 Resumen

El servicio ETL con cron ejecuta automáticamente cargas incrementales de datos cada viernes a las 23:00 (hora Colombia). Además, verifica diariamente si hay cargas pendientes y las ejecuta automáticamente.

---

## 🛠️ Construcción e Inicio

### **Paso 1: Construir el contenedor ETL**

```bash
cd "C:\Users\Rai De  León\Documents\1Projects\Homicidios\ML-Homicidios"

# Construir solo el servicio ETL
docker-compose build etl-cron
```

### **Paso 2: Iniciar todos los servicios**

```bash
# Iniciar todos los servicios (incluido ETL)
docker-compose up -d

# Ver logs del servicio ETL
docker-compose logs -f etl-cron
```

---

## 📊 Verificar Estado

### **Ver logs en tiempo real:**

```bash
# Logs del contenedor
docker-compose logs -f etl-cron

# Logs de cron (ejecuciones programadas)
docker exec ml-homicidios-etl-cron tail -f /app/logs/cron.log

# Logs de catch-up (recuperación de cargas perdidas)
docker exec ml-homicidios-etl-cron tail -f /app/logs/catchup.log

# Logs de health check
docker exec ml-homicidios-etl-cron tail -f /app/logs/health.log
```

### **Ver cron jobs configurados:**

```bash
docker exec ml-homicidios-etl-cron crontab -l
```

---

## 🧪 Pruebas Manuales

### **Ejecutar carga incremental manualmente:**

```bash
docker exec ml-homicidios-etl-cron python scripts/load_datalake.py --incremental
```

### **Ejecutar verificación de catch-up:**

```bash
docker exec ml-homicidios-etl-cron python scripts/catchup_check.py
```

### **Ejecutar health check:**

```bash
docker exec ml-homicidios-etl-cron python scripts/health_check.py
```

---

## 📅 Horarios Programados

| Tarea | Frecuencia | Hora | Descripción |
|-------|------------|------|-------------|
| **Carga Incremental** | Semanal (Viernes) | 23:00 | Extrae nuevos homicidios desde API |
| **Verificación Catch-up** | Diaria | 08:00 | Detecta cargas perdidas y las ejecuta |
| **Health Check** | Diaria | 02:00 | Verifica estado del sistema |
| **Limpieza de Logs** | Semanal (Domingo) | 03:00 | Elimina logs > 30 días |

---

## 🔍 Monitoreo

### **Ver últimas cargas:**

```bash
docker exec ml-homicidios-etl-cron python -c "
from src.data_ingestion.db_connection import DatabaseConnection
db = DatabaseConnection()
results = db.execute_query('''
    SELECT dataset_name, load_completed_at, records_loaded, status
    FROM data_load_log
    ORDER BY load_completed_at DESC
    LIMIT 5
''', fetch=True)
for row in results:
    print(row)
db.close_all_connections()
"
```

---

## 🛑 Detener y Reiniciar

### **Detener servicio ETL:**

```bash
docker-compose stop etl-cron
```

### **Reiniciar servicio ETL:**

```bash
docker-compose restart etl-cron
```

### **Detener todos los servicios:**

```bash
docker-compose down
```

---

## 🔧 Troubleshooting

### **Problema: Cron no se ejecuta**

**Verificar que el daemon esté corriendo:**
```bash
docker exec ml-homicidios-etl-cron pgrep crond
```

**Ver logs del cron:**
```bash
docker-compose logs etl-cron
```

### **Problema: No hay conexión a base de datos**

**Verificar que Data Lake esté corriendo:**
```bash
docker-compose ps datalake
```

**Probar conexión manualmente:**
```bash
docker exec ml-homicidios-etl-cron pg_isready -h datalake -p 5432 -U datalake_user
```

### **Problema: Catch-up no detecta cargas pendientes**

**Ejecutar manualmente para ver detalles:**
```bash
docker exec ml-homicidios-etl-cron python scripts/catchup_check.py
```

---

## 📝 Archivos de Logs

Los logs se guardan en: `./logs/`

| Archivo | Contenido |
|---------|-----------|
| `cron.log` | Ejecuciones del cron semanal |
| `catchup.log` | Ejecuciones de catch-up automático |
| `health.log` | Resultados de health checks |
| `ml_homicidios.log` | Logs generales de la aplicación |

---

## 🎯 Escenarios de Uso

### **Escenario 1: Contenedor corriendo normalmente**
- ✅ Viernes 23:00 → Carga automática
- ✅ Sábado 08:00 → Verificación (todo al día)
- ✅ Próximo viernes → Carga automática

### **Escenario 2: Contenedor apagado 2 semanas**
- ❌ Viernes 15 Nov → Última carga
- 🔴 Contenedor APAGADO
- ✅ Jueves 5 Dic → Enciendes contenedor
  - Al iniciar: Detecta 20 días sin carga
  - Ejecuta catch-up automático
  - Trae TODOS los datos desde Nov 15
- ✅ Sistema actualizado

### **Escenario 3: Falla en carga del viernes**
- ❌ Viernes 23:00 → Carga falla (API caída)
- ✅ Sábado 08:00 → Verificación detecta falla
- ✅ Sábado 08:00 → Ejecuta catch-up automático
- ✅ Sistema recuperado

---

## 🚀 Comandos Útiles

```bash
# Ver estado de todos los servicios
docker-compose ps

# Ver logs de todos los servicios
docker-compose logs

# Reconstruir servicio ETL (después de cambios en código)
docker-compose build etl-cron
docker-compose up -d etl-cron

# Acceder al contenedor (shell interactivo)
docker exec -it ml-homicidios-etl-cron sh

# Ver uso de recursos
docker stats ml-homicidios-etl-cron
```

---

¡El servicio ETL está listo para funcionar automáticamente! 🎉
