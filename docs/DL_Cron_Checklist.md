# ✅ Checklist: Implementación del Servicio ETL con Cron

## 📋 Archivos Creados

- [x] `docker/Dockerfile.etl` - Dockerfile para servicio ETL
- [x] `docker/entrypoint-cron.sh` - Script de inicio con catch-up automático
- [x] `docker/crontab` - Configuración de cron jobs
- [x] `scripts/catchup_check.py` - Verificación de cargas pendientes
- [x] `scripts/health_check.py` - Health check del sistema
- [x] `docker-compose.yml` - Actualizado con servicio ETL
- [x] `docs/ETL_CRON_USAGE.md` - Guía de uso

---

## 🚀 Pasos para Activar el Servicio

### **1. Construir el contenedor ETL**

```bash
cd "C:\Users\Rai De  León\Documents\1Projects\Homicidios\ML-Homicidios"
docker-compose build etl-cron
```

### **2. Iniciar todos los servicios**

```bash
docker-compose up -d
```

### **3. Verificar que el servicio está corriendo**

```bash
# Ver estado
docker-compose ps

# Ver logs
docker-compose logs -f etl-cron
```

**Deberías ver:**
```
✅ Data Lake disponible
✅ Sistema al día, no hay cargas pendientes
📅 Cron jobs configurados
⏰ Iniciando cron daemon...
```

---

## 🧪 Pruebas Recomendadas

### **Prueba 1: Verificar cron jobs**

```bash
docker exec ml-homicidios-etl-cron crontab -l
```

**Resultado esperado:**
```
0 23 * * 5 cd /app && python scripts/load_datalake.py --incremental >> /app/logs/cron.log 2>&1
0 8 * * * cd /app && python scripts/catchup_check.py ...
0 2 * * * cd /app && python scripts/health_check.py ...
0 3 * * 0 find /app/logs -name "*.log" -mtime +30 -delete
```

### **Prueba 2: Ejecutar catch-up check manualmente**

```bash
docker exec ml-homicidios-etl-cron python scripts/catchup_check.py
```

**Resultado esperado:**
```
======================================================================
VERIFICACIÓN DE CARGAS PENDIENTES
======================================================================
📅 Última carga: 2025-11-22 18:00:00
📊 Días sin carga: 0
✅ Sistema al día, no hay cargas pendientes
======================================================================
🟢 Resultado: SISTEMA AL DÍA
======================================================================
```

### **Prueba 3: Ejecutar health check**

```bash
docker exec ml-homicidios-etl-cron python scripts/health_check.py
```

**Resultado esperado:**
```
======================================================================
HEALTH CHECK - SISTEMA ETL
======================================================================
✅ Data Lake: Conexión OK
📊 Últimas 10 cargas:
✅ raw_homicidios | incremental | 332131 registros | 2025-11-22 18:00
...
======================================================================
✅ HEALTH CHECK COMPLETADO
======================================================================
```

### **Prueba 4: Simular carga incremental**

```bash
docker exec ml-homicidios-etl-cron python scripts/load_datalake.py --incremental
```

---

## 🔍 Verificar Logs

```bash
# Logs del contenedor
docker-compose logs etl-cron

# Logs de cron (en el host)
cat logs/cron.log

# Logs de catch-up
cat logs/catchup.log

# Logs de health check
cat logs/health.log
```

---

## ✅ Checklist de Verificación

- [ ] Contenedor ETL construido correctamente
- [ ] Contenedor ETL corriendo (`docker-compose ps`)
- [ ] Cron daemon activo (`pgrep crond`)
- [ ] Cron jobs configurados (4 jobs)
- [ ] Catch-up check funciona
- [ ] Health check funciona
- [ ] Conexión a Data Lake OK
- [ ] Logs se crean en `./logs/`

---

## 🎯 Comportamiento Esperado

### **Al iniciar el contenedor:**
1. ✅ Verifica conexión a Data Lake
2. ✅ Ejecuta catch-up check
3. ✅ Si hay cargas pendientes, las ejecuta automáticamente
4. ✅ Inicia cron daemon
5. ✅ Queda esperando próxima ejecución programada

### **Cada viernes a las 23:00:**
1. ✅ Cron ejecuta carga incremental
2. ✅ Extrae nuevos registros desde API
3. ✅ Inserta en Data Lake
4. ✅ Registra en `data_load_log`
5. ✅ Guarda logs en `cron.log`

### **Cada día a las 08:00:**
1. ✅ Verifica si hay cargas pendientes
2. ✅ Si detecta cargas perdidas, las ejecuta
3. ✅ Registra en `catchup.log`

### **Cada día a las 02:00:**
1. ✅ Ejecuta health check
2. ✅ Verifica conexión y últimas cargas
3. ✅ Registra en `health.log`

---

## 🚨 Troubleshooting

### **Error: "Cannot connect to Data Lake"**

**Solución:**
```bash
# Verificar que Data Lake esté corriendo
docker-compose ps datalake

# Reiniciar Data Lake
docker-compose restart datalake

# Reiniciar ETL
docker-compose restart etl-cron
```

### **Error: "Cron daemon not running"**

**Solución:**
```bash
# Ver logs
docker-compose logs etl-cron

# Reconstruir contenedor
docker-compose build etl-cron
docker-compose up -d etl-cron
```

### **Logs no se crean**

**Solución:**
```bash
# Verificar que el directorio logs existe
mkdir -p logs

# Dar permisos
chmod 777 logs

# Reiniciar contenedor
docker-compose restart etl-cron
```

---

## 📝 Próximos Pasos

Después de verificar que todo funciona:

1. ✅ Dejar el contenedor corriendo 24/7
2. ✅ Monitorear logs semanalmente
3. ✅ Verificar cargas cada viernes
4. ✅ Revisar health checks periódicamente

---

¡El servicio ETL con cron está listo para producción! 🎉
