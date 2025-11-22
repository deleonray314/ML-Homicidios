# 🐳 Acceso a Bases de Datos en Docker

## 🔒 Arquitectura de Seguridad

Las bases de datos **NO están expuestas** directamente al host ni a la red local.

### ✅ Cómo Funciona

```
┌─────────────────────────────────────────┐
│         Red Docker Interna              │
│  (ml-homicidios-network)                │
│                                         │
│  ┌──────────┐    ┌──────────────┐     │
│  │ Data     │◄───┤ Aplicación   │     │
│  │ Lake     │    │ Python       │     │
│  └──────────┘    └──────────────┘     │
│                                         │
│  ┌──────────┐    ┌──────────────┐     │
│  │ Data     │◄───┤ pgAdmin      │◄────┼─── Puerto 5050 (Web)
│  │Warehouse │    │              │     │
│  └──────────┘    └──────────────┘     │
│                                         │
└─────────────────────────────────────────┘

❌ NO hay acceso directo desde el host
✅ Solo contenedores en la red Docker pueden conectarse
✅ pgAdmin es el único punto de acceso externo (interfaz web)
```

---

## 🎯 Formas de Acceder a las Bases de Datos

### 1. **Desde pgAdmin (Interfaz Web)** ✅ RECOMENDADO

**Acceso**: http://localhost:5050

**Credenciales**:
- Email: `admin@homicidios.local`
- Password: `admin123`

**Conexión a bases de datos**:
- Host: `datalake` (nombre del contenedor, NO localhost)
- Port: `5432` (puerto interno de Docker)
- User: `datalake_user`
- Password: `datalake_password_2024`

### 2. **Desde un Contenedor de Aplicación Python**

Crea un servicio en `docker-compose.yml`:

```yaml
  app:
    build: .
    container_name: ml-homicidios-app
    networks:
      - ml-homicidios-network
    environment:
      DB_HOST: datalake  # Nombre del contenedor
      DB_PORT: 5432      # Puerto interno
      DB_NAME: homicidios_datalake
      DB_USER: datalake_user
      DB_PASSWORD: datalake_password_2024
    depends_on:
      - datalake
      - datawarehouse
```

Desde Python en el contenedor:

```python
import psycopg2

conn = psycopg2.connect(
    host="datalake",  # Nombre del contenedor
    port=5432,        # Puerto interno
    database="homicidios_datalake",
    user="datalake_user",
    password="datalake_password_2024"
)
```

### 3. **Desde docker exec (Línea de Comandos)**

```bash
# Ejecutar psql dentro del contenedor
docker exec -it ml-homicidios-datalake psql -U datalake_user -d homicidios_datalake

# Ejecutar query directamente
docker exec -it ml-homicidios-datalake psql -U datalake_user -d homicidios_datalake -c "SELECT COUNT(*) FROM raw_homicidios;"
```

### 4. **Port Forwarding Temporal (Solo para Desarrollo)**

Si necesitas acceso temporal desde tu máquina:

```bash
# Crear un túnel SSH/port forward
docker exec -it ml-homicidios-datalake bash

# O usar docker port forwarding
docker run -it --rm --network ml-homicidios-network postgres:15-alpine psql -h datalake -U datalake_user -d homicidios_datalake
```

---

## 🔐 Ventajas de Esta Configuración

| Aspecto | Beneficio |
|---------|-----------|
| **Seguridad** | Bases de datos no expuestas a la red |
| **Aislamiento** | Solo contenedores autorizados pueden acceder |
| **Simplicidad** | No necesitas configurar firewall |
| **Portabilidad** | Funciona igual en cualquier máquina |
| **Producción-ready** | Arquitectura similar a la de producción |

---

## 📊 Conexiones Disponibles

### Desde el Host (tu computadora)

| Servicio | ¿Accesible? | Método |
|----------|-------------|--------|
| Data Lake | ❌ No | Solo vía pgAdmin o docker exec |
| Data Warehouse | ❌ No | Solo vía pgAdmin o docker exec |
| pgAdmin | ✅ Sí | http://localhost:5050 |

### Desde Contenedores Docker

| Servicio | Host | Puerto | ¿Accesible? |
|----------|------|--------|-------------|
| Data Lake | `datalake` | 5432 | ✅ Sí |
| Data Warehouse | `datawarehouse` | 5432 | ✅ Sí |
| pgAdmin | `pgadmin` | 80 | ✅ Sí |

---

## 🛠️ Crear Contenedor de Aplicación Python

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

CMD ["python", "main.py"]
```

### Agregar a docker-compose.yml

```yaml
  app:
    build: .
    container_name: ml-homicidios-app
    volumes:
      - ./src:/app/src
      - ./data:/app/data
    networks:
      - ml-homicidios-network
    environment:
      # Conexión a Data Lake
      DATALAKE_HOST: datalake
      DATALAKE_PORT: 5432
      DATALAKE_DB: homicidios_datalake
      DATALAKE_USER: datalake_user
      DATALAKE_PASSWORD: datalake_password_2024
      
      # Conexión a Data Warehouse
      DW_HOST: datawarehouse
      DW_PORT: 5432
      DW_DB: homicidios_dw
      DW_USER: dw_user
      DW_PASSWORD: dw_password_2024
    depends_on:
      datalake:
        condition: service_healthy
      datawarehouse:
        condition: service_healthy
```

### Iniciar aplicación

```bash
docker-compose up -d app
```

---

## 🧪 Ejemplos de Uso

### Ejecutar Script Python en Contenedor

```bash
# Ejecutar script que se conecta a la base de datos
docker-compose run --rm app python scripts/load_data.py
```

### Ejecutar Query SQL

```bash
# Desde Data Lake
docker exec -it ml-homicidios-datalake psql -U datalake_user -d homicidios_datalake -c "
SELECT 
    departamento,
    COUNT(*) as total
FROM raw_homicidios
GROUP BY departamento
ORDER BY total DESC
LIMIT 10;
"
```

### Backup de Base de Datos

```bash
# Crear backup
docker exec ml-homicidios-datalake pg_dump -U datalake_user homicidios_datalake > backup.sql

# Restaurar backup
docker exec -i ml-homicidios-datalake psql -U datalake_user homicidios_datalake < backup.sql
```

---

## 🔓 Si Necesitas Acceso Directo (No Recomendado)

Si realmente necesitas acceso directo desde el host, descomenta en `docker-compose.yml`:

```yaml
datalake:
  ports:
    - "127.0.0.1:5433:5432"  # Solo localhost
    # o
    - "0.0.0.0:5433:5432"    # Toda la red
```

**Reinicia el servicio**:
```bash
docker-compose restart datalake
```

---

## 📝 Mejores Prácticas

1. **✅ Usar pgAdmin** para administración y queries ad-hoc
2. **✅ Crear contenedor de aplicación** para scripts Python
3. **✅ Usar docker exec** para comandos rápidos
4. **❌ NO exponer** puertos de bases de datos al host en producción
5. **✅ Usar redes Docker** para comunicación entre contenedores

---

## 🎯 Resumen

- **Bases de datos**: Solo accesibles desde red Docker interna
- **pgAdmin**: Accesible desde http://localhost:5050
- **Aplicaciones Python**: Deben correr en contenedores Docker
- **Seguridad**: Máxima, bases de datos no expuestas

¿Necesitas ayuda creando el contenedor de aplicación Python? 🐍
