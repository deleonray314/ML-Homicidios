# Guía Rápida: Iniciar Docker

## 🚀 Pasos para Iniciar

### 1. Verificar que Docker esté instalado

```bash
docker --version
docker-compose --version
```

### 2. Actualizar archivo .env

Asegúrate de que tu `.env` tenga las credenciales de Docker:

```bash
# Copiar desde .env.example si es necesario
cp .env.example .env
```

### 3. Iniciar servicios

```bash
# Iniciar en segundo plano
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f
```

### 4. Verificar que todo esté corriendo

```bash
docker-compose ps
```

Deberías ver 3 servicios con estado "Up (healthy)":

- `ml-homicidios-datalake`
- `ml-homicidios-datawarehouse`
- `ml-homicidios-adminer`

### 5. Acceder a Adminer

1. Abre: http://localhost:8080
2. Conectarse a Data Lake:
   - Sistema: PostgreSQL
   - Servidor: `datalake`
   - Usuario: `datalake_user`
   - Contraseña: `datalake_password_2024`
   - Base de datos: `homicidios_datalake`

### 6. Explorar las Tablas

En Adminer verás las tablas creadas:

- `raw_homicidios`
- `raw_divipola_departamentos`
- `raw_divipola_municipios`
- `data_load_log`

---

## 🛑 Detener Servicios

```bash
# Detener sin borrar datos
docker-compose down

# Detener Y borrar todos los datos (⚠️ CUIDADO)
docker-compose down -v
```

---

## 📊 Verificar Tablas Creadas

```bash
# Conectar a Data Lake
docker exec -it ml-homicidios-datalake psql -U datalake_user -d homicidios_datalake -c "\dt"

# Conectar a Data Warehouse
docker exec -it ml-homicidios-datawarehouse psql -U dw_user -d homicidios_dw -c "\dt"
```

## 🔧 Troubleshooting

**Error: "Cannot connect to Docker daemon"**

- Asegúrate de que Docker Desktop esté corriendo

**Las tablas no se crearon**

- Verifica los logs: `docker-compose logs datalake`
- Elimina el volumen y reinicia: `docker-compose down -v && docker-compose up -d`
