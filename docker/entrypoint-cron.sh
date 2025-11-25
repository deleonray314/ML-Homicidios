#!/bin/sh
# No usar set -e para evitar que el script termine en catch-up

echo "=========================================="
echo "🚀 ETL Cron Service - ML Homicidios"
echo "=========================================="
echo "Timezone: $TZ"
echo "Fecha actual: $(date)"
echo "=========================================="

# Verificar conexión a base de datos
echo "🔌 Verificando conexión a Data Lake..."
until pg_isready -h datalake -p 5432 -U datalake_user; do
  echo "⏳ Esperando a que Data Lake esté disponible..."
  sleep 2
done
echo "✅ Data Lake disponible"

# ============================================
# CATCH-UP AUTOMÁTICO AL INICIO
# ============================================
echo ""
echo "=========================================="
echo "🔍 Verificando cargas perdidas..."
echo "=========================================="

# Ejecutar script de catch-up (no bloquear si falla)
python /app/scripts/catchup_check.py || true
CATCHUP_RESULT=$?

if [ $CATCHUP_RESULT -eq 1 ]; then
    echo ""
    echo "⚠️  CARGAS PENDIENTES DETECTADAS"
    echo "🔄 Ejecutando carga incremental de recuperación..."
    echo ""
    
    python /app/scripts/load_datalake.py --incremental || echo "⚠️ Catch-up falló, se reintentará en próxima verificación"
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Catch-up completado exitosamente"
    fi
else
    echo "✅ Sistema al día, no hay cargas pendientes"
fi

echo "=========================================="
echo ""

# Mostrar cron jobs configurados
echo "📅 Cron jobs configurados:"
echo "=========================================="
crontab -l
echo "=========================================="
echo ""

# Registrar inicio en log
echo "[$(date)] ✅ ETL Cron Service iniciado" >> /app/logs/cron.log
echo "[$(date)] Próxima carga programada: Viernes 23:00" >> /app/logs/cron.log

# Mensaje final
echo "🎯 Servicio ETL iniciado correctamente"
echo "📊 Carga incremental: Cada viernes a las 23:00"
echo "🔍 Verificación diaria: Cada día a las 08:00"
echo "📝 Logs disponibles en: /app/logs/"
echo ""
echo "=========================================="
echo "⏰ Iniciando cron daemon..."
echo "=========================================="

# Iniciar cron en background
crond -l 2

# Mantener contenedor vivo con loop infinito
echo "✅ Cron daemon iniciado en background"
echo "🔄 Manteniendo contenedor activo..."

# Loop infinito para mantener contenedor corriendo
while true; do
    sleep 3600  # Dormir 1 hora
done
