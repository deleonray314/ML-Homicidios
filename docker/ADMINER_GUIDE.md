# 🚀 Guía Rápida: Adminer

## 🌐 Acceso a Adminer

**URL**: http://localhost:8080

---

## 🔐 Conectarse a las Bases de Datos

### Data Lake

1. Abre: http://localhost:8080
2. Selecciona:
   - **Sistema**: PostgreSQL
   - **Servidor**: `datalake`
   - **Usuario**: `datalake_user`
   - **Contraseña**: `datalake_password_2024`
   - **Base de datos**: `homicidios_datalake`
3. Click en **Entrar**

### Data Warehouse

1. Abre: http://localhost:8080
2. Selecciona:
   - **Sistema**: PostgreSQL
   - **Servidor**: `datawarehouse`
   - **Usuario**: `dw_user`
   - **Contraseña**: `dw_password_2024`
   - **Base de datos**: `homicidios_dw`
3. Click en **Entrar**

---

## 📊 Funcionalidades Principales

### Ver Tablas

1. Conectarse a la base de datos
2. En el menú izquierdo, verás todas las tablas
3. Click en una tabla para ver su estructura

### Ejecutar Queries

1. Click en **Comando SQL** (arriba)
2. Escribe tu query:
   ```sql
   SELECT * FROM raw_homicidios LIMIT 10;
   ```
3. Click en **Ejecutar**

### Exportar Datos

1. Click en una tabla
2. Click en **Exportar** (arriba)
3. Selecciona formato (CSV, SQL, JSON)
4. Click en **Exportar**

### Importar Datos

1. Click en **Importar** (arriba)
2. Selecciona archivo
3. Click en **Ejecutar**

---

## 🎨 Cambiar Tema

Adminer tiene varios temas disponibles. Para cambiar:

1. En la pantalla de login, abajo hay un selector de diseño
2. Opciones populares:
   - `pepa-linha` (moderno, oscuro)
   - `nette` (claro, minimalista)
   - `hydra` (azul)

O modifica en `docker-compose.yml`:

```yaml
environment:
  ADMINER_DESIGN: pepa-linha  # Cambiar aquí
```

---

## 💡 Tips Útiles

### Atajos de Teclado

- `Ctrl + Enter` - Ejecutar query
- `Ctrl + S` - Guardar query

### Queries Frecuentes

**Contar registros**:
```sql
SELECT COUNT(*) FROM raw_homicidios;
```

**Ver últimos registros**:
```sql
SELECT * FROM raw_homicidios 
ORDER BY loaded_at DESC 
LIMIT 10;
```

**Ver estructura de tabla**:
```sql
\d raw_homicidios
```

---

## 🔄 Cambiar entre Bases de Datos

1. Click en el nombre de la base de datos (arriba izquierda)
2. Verás la pantalla de login
3. Cambia el servidor y credenciales
4. Click en **Entrar**

---

## 📝 Ventajas de Adminer

- ⚡ **Súper rápido** - Carga instantánea
- 🎯 **Interfaz simple** - Fácil de usar
- 💾 **Ligero** - Solo 90 MB
- 🔄 **Multi-DB** - Soporta PostgreSQL, MySQL, SQLite, etc.
- 📱 **Responsive** - Funciona en móviles

---

## 🆚 Comparación con pgAdmin

| Característica | Adminer | pgAdmin |
|----------------|---------|---------|
| Tamaño | 90 MB | 400 MB |
| Velocidad | ⚡⚡⚡ | ⚡ |
| Interfaz | Simple | Compleja |
| Funcionalidades | Básicas | Avanzadas |

---

## 🛠️ Troubleshooting

### No puedo conectarme

**Verifica**:
1. Docker está corriendo: `docker-compose ps`
2. Nombre del servidor es correcto: `datalake` o `datawarehouse` (NO `localhost`)
3. Credenciales son correctas (revisa `.env`)

### Error: "Connection refused"

**Solución**:
```bash
# Reiniciar servicios
docker-compose restart datalake datawarehouse adminer
```

### Adminer no carga

**Solución**:
```bash
# Ver logs
docker-compose logs adminer

# Reiniciar
docker-compose restart adminer
```

---

## 🎯 Resumen Rápido

1. **URL**: http://localhost:8080
2. **Servidor Data Lake**: `datalake`
3. **Servidor Data Warehouse**: `datawarehouse`
4. **Usuario Data Lake**: `datalake_user`
5. **Usuario Data Warehouse**: `dw_user`
6. **Contraseñas**: Ver `.env`

---

¡Listo para usar! 🚀
