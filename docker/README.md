# 🐳 Docker - Guía de Uso

## 📋 Servicios Disponibles

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| **Data Lake** | 5433 | PostgreSQL - Datos crudos |
| **Data Warehouse** | 5434 | PostgreSQL - Modelo estrella |
| **pgAdmin** | 5050 | Interfaz web de administración |

---

## 🚀 Comandos Básicos

### Iniciar todos los servicios

```bash
docker-compose up -d
```

### Ver logs de los servicios

```bash
# Todos los servicios
docker-compose logs -f

# Solo Data Lake
docker-compose logs -f datalake

# Solo Data Warehouse
docker-compose logs -f datawarehouse
```

### Detener servicios

```bash
docker-compose down
```

### Detener y eliminar volúmenes (⚠️ BORRA TODOS LOS DATOS)

```bash
docker-compose down -v
```

### Reiniciar un servicio específico

```bash
docker-compose restart datalake
```

---

## 🔧 Conexión a las Bases de Datos

### Desde la aplicación Python

Las credenciales ya están configuradas en `.env`:

```python
from src.config.settings import settings

# Data Lake
datalake_url = settings.get_database_url()
# postgresql://datalake_user:datalake_password_2024@localhost:5433/homicidios_datalake
```

### Desde psql (línea de comandos)

```bash
# Data Lake
psql -h localhost -p 5433 -U datalake_user -d homicidios_datalake

# Data Warehouse
psql -h localhost -p 5434 -U dw_user -d homicidios_dw
```

### Desde pgAdmin (interfaz web)

1. Abre tu navegador: http://localhost:5050
2. Login:
   - Email: `admin@homicidios.local`
   - Password: `admin123`
3. Agregar servidor:
   - **Data Lake**:
     - Host: `datalake` (nombre del contenedor)
     - Port: `5432` (puerto interno)
     - User: `datalake_user`
     - Password: `datalake_password_2024`
   - **Data Warehouse**:
     - Host: `datawarehouse`
     - Port: `5432`
     - User: `dw_user`
     - Password: `dw_password_2024`

---

## 📊 Esquemas de Base de Datos

### Data Lake

Tablas:
- `raw_homicidios` - Datos crudos de homicidios
- `raw_divipola_departamentos` - Catálogo de departamentos
- `raw_divipola_municipios` - Catálogo de municipios
- `data_load_log` - Log de cargas

### Data Warehouse

Tablas:
- `fact_homicidios` - Tabla de hechos
- `dim_fecha` - Dimensión temporal
- `dim_ubicacion` - Dimensión geográfica
- `dim_victima` - Dimensión demográfica
- `dim_arma` - Dimensión de armas
- `etl_log` - Log de ETL

Vistas:
- `v_homicidios_por_mes`
- `v_homicidios_por_departamento`
- `v_homicidios_por_sexo`

---

## 🔍 Verificar Estado de los Servicios

```bash
# Ver contenedores en ejecución
docker-compose ps

# Verificar salud de los servicios
docker-compose ps | grep healthy
```

---

## 🛠️ Troubleshooting

### Error: Puerto ya en uso

Si recibes un error como `port is already allocated`:

```bash
# Verificar qué está usando el puerto
netstat -ano | findstr :5433

# Cambiar el puerto en docker-compose.yml
# Ejemplo: "5435:5432" en lugar de "5433:5432"
```

### Resetear base de datos

```bash
# 1. Detener servicios
docker-compose down

# 2. Eliminar volúmenes
docker volume rm ml-homicidios-datalake-data
docker volume rm ml-homicidios-datawarehouse-data

# 3. Reiniciar
docker-compose up -d
```

### Ver logs de inicialización

```bash
# Ver si los scripts SQL se ejecutaron correctamente
docker-compose logs datalake | grep "database system is ready"
docker-compose logs datawarehouse | grep "database system is ready"
```

---

## 📝 Notas Importantes

1. **Puertos mapeados**:
   - Data Lake: `5433` (host) → `5432` (container)
   - Data Warehouse: `5434` (host) → `5432` (container)
   - Esto evita conflictos con PostgreSQL local

2. **Persistencia**:
   - Los datos se guardan en volúmenes Docker
   - Sobreviven a `docker-compose down`
   - Se eliminan solo con `docker-compose down -v`

3. **Scripts de inicialización**:
   - Se ejecutan automáticamente al crear el contenedor
   - Solo se ejecutan la primera vez
   - Para re-ejecutar, elimina el volumen

4. **Seguridad**:
   - Cambia las contraseñas en `.env` para producción
   - No uses las contraseñas por defecto en producción

---

## 🎯 Próximos Pasos

Después de iniciar Docker:

1. Verificar que los servicios estén corriendo
2. Conectarse a pgAdmin y explorar las tablas
3. Ejecutar el primer script de carga de datos
4. Verificar que los datos se cargaron correctamente
