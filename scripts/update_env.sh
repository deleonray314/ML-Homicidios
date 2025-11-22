#!/bin/bash
# Script para actualizar .env desde .env.example
# Uso: bash scripts/update_env.sh

echo "🔧 Actualizando archivo .env..."

# Verificar si .env existe
if [ -f .env ]; then
    echo "⚠️  El archivo .env ya existe."
    read -p "¿Deseas respaldarlo antes de actualizar? (y/n): " backup
    
    if [ "$backup" = "y" ]; then
        cp .env .env.backup
        echo "✅ Respaldo creado: .env.backup"
    fi
fi

# Copiar .env.example a .env
cp .env.example .env

echo "✅ Archivo .env actualizado desde .env.example"
echo ""
echo "📝 IMPORTANTE: Ahora debes editar .env y agregar tus dataset IDs:"
echo ""
echo "  1. Abre el archivo .env"
echo "  2. Busca las siguientes líneas:"
echo "     DATOS_ABIERTOS_HOMICIDIOS_ID="
echo "     DATOS_ABIERTOS_DIVIPOLA_DEPARTAMENTOS_ID="
echo "     DATOS_ABIERTOS_DIVIPOLA_MUNICIPIOS_ID="
echo ""
echo "  3. Agrega los IDs que obtuviste de datos.gov.co"
echo ""
echo "💡 Ejemplo:"
echo "     DATOS_ABIERTOS_HOMICIDIOS_ID=abcd-1234"
echo ""
