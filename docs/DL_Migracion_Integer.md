# 🔄 Guía: Convertir Códigos a INTEGER y Agregar Foreign Keys

## 📋 Resumen

Esta guía te ayudará a convertir los códigos de departamento y municipio de VARCHAR a INTEGER en el Data Lake existente, y luego agregar las foreign keys para establecer relaciones entre tablas.

---

## ⚠️ IMPORTANTE: Backup Primero

Antes de hacer cualquier cambio, haz un backup de los datos:

```bash
# Backup completo de la base de datos
docker exec ml-homicidios-datalake pg_dump -U datalake_user homicidios_datalake > backup_datalake_$(date +%Y%m%d).sql
```

---

## 🔧 Opción 1: Recrear Base de Datos (RECOMENDADO)

Esta es la opción más limpia. Vas a eliminar y recrear la base de datos con el nuevo schema.

### Paso 1: Detener Docker

```bash
cd "C:\Users\Rai De  León\Documents\1Projects\Homicidios\ML-Homicidios"
docker-compose down
```

### Paso 2: Eliminar Volúmenes

```bash
docker volume rm ml-homicidios-datalake-data
```

### Paso 3: Reiniciar Docker

```bash
docker-compose up -d
```

El nuevo schema (con INTEGER) se aplicará automáticamente.

### Paso 4: Recargar Datos

```bash
# Cargar todos los datasets
python scripts/load_datalake.py --initial
```

### Paso 5: Agregar Foreign Keys

Ejecuta este script en DBeaver:

```sql
-- Agregar FOREIGN KEYS
ALTER TABLE raw_homicidios 
ADD CONSTRAINT fk_homicidios_departamento 
    FOREIGN KEY (cod_depto) 
    REFERENCES raw_divipola_departamentos(cod_dpto)
    ON DELETE RESTRICT
    ON UPDATE CASCADE;

ALTER TABLE raw_homicidios 
ADD CONSTRAINT fk_homicidios_municipio 
    FOREIGN KEY (cod_muni) 
    REFERENCES raw_divipola_municipios(cod_mpio)
    ON DELETE RESTRICT
    ON UPDATE CASCADE;

-- Crear índices
CREATE INDEX idx_homicidios_cod_depto ON raw_homicidios(cod_depto);
CREATE INDEX idx_homicidios_cod_muni ON raw_homicidios(cod_muni);

-- Verificar
SELECT
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name AS foreign_table,
    ccu.column_name AS foreign_column
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
    AND tc.table_name = 'raw_homicidios';
```

---

## 🔧 Opción 2: Migración In-Place (SIN recrear)

Si quieres mantener los datos actuales y solo cambiar los tipos.

### Paso 1: Convertir Tipos en Departamentos

```sql
ALTER TABLE raw_divipola_departamentos 
ALTER COLUMN cod_dpto TYPE INTEGER USING cod_dpto::INTEGER;
```

### Paso 2: Convertir Tipos en Municipios

```sql
ALTER TABLE raw_divipola_municipios 
ALTER COLUMN cod_dpto TYPE INTEGER USING cod_dpto::INTEGER;

ALTER TABLE raw_divipola_municipios 
ALTER COLUMN cod_mpio TYPE INTEGER USING cod_mpio::INTEGER;
```

### Paso 3: Convertir Tipos en Homicidios

```sql
ALTER TABLE raw_homicidios 
ALTER COLUMN cod_depto TYPE INTEGER USING cod_depto::INTEGER;

ALTER TABLE raw_homicidios 
ALTER COLUMN cod_muni TYPE INTEGER USING cod_muni::INTEGER;
```

### Paso 4: Agregar Foreign Keys

```sql
ALTER TABLE raw_homicidios 
ADD CONSTRAINT fk_homicidios_departamento 
    FOREIGN KEY (cod_depto) 
    REFERENCES raw_divipola_departamentos(cod_dpto)
    ON DELETE RESTRICT
    ON UPDATE CASCADE;

ALTER TABLE raw_homicidios 
ADD CONSTRAINT fk_homicidios_municipio 
    FOREIGN KEY (cod_muni) 
    REFERENCES raw_divipola_municipios(cod_mpio)
    ON DELETE RESTRICT
    ON UPDATE CASCADE;
```

### Paso 5: Crear Índices

```sql
CREATE INDEX idx_homicidios_cod_depto ON raw_homicidios(cod_depto);
CREATE INDEX idx_homicidios_cod_muni ON raw_homicidios(cod_muni);
```

---

## ✅ Verificación

### 1. Verificar Tipos de Datos

```sql
SELECT 
    table_name, 
    column_name, 
    data_type 
FROM information_schema.columns
WHERE table_name IN ('raw_homicidios', 'raw_divipola_departamentos', 'raw_divipola_municipios')
    AND column_name IN ('cod_depto', 'cod_dpto', 'cod_muni', 'cod_mpio')
ORDER BY table_name, column_name;
```

**Resultado esperado:**
```
table_name                   | column_name | data_type
-----------------------------+-------------+-----------
raw_divipola_departamentos   | cod_dpto    | integer
raw_divipola_municipios      | cod_dpto    | integer
raw_divipola_municipios      | cod_mpio    | integer
raw_homicidios               | cod_depto   | integer
raw_homicidios               | cod_muni    | integer
```

### 2. Verificar Foreign Keys

```sql
SELECT
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name AS foreign_table,
    ccu.column_name AS foreign_column
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
    AND tc.table_name = 'raw_homicidios';
```

**Resultado esperado:**
```
constraint_name              | column_name | foreign_table                | foreign_column
-----------------------------+-------------+------------------------------+---------------
fk_homicidios_departamento   | cod_depto   | raw_divipola_departamentos   | cod_dpto
fk_homicidios_municipio      | cod_muni    | raw_divipola_municipios      | cod_mpio
```

### 3. Probar Relaciones

```sql
-- Contar homicidios por departamento con JOIN
SELECT 
    d.cod_dpto,
    d.nom_dpto,
    COUNT(h.id) as total_homicidios
FROM raw_divipola_departamentos d
LEFT JOIN raw_homicidios h ON d.cod_dpto = h.cod_depto
GROUP BY d.cod_dpto, d.nom_dpto
ORDER BY total_homicidios DESC
LIMIT 10;
```

---

## 📊 Cambios Realizados en el Código

### ✅ Archivos Actualizados:

1. **`docker/init-scripts/01-create-datalake-schema.sql`**
   - Cambiado `cod_depto` de `VARCHAR(2)` a `INTEGER`
   - Cambiado `cod_muni` de `VARCHAR(5)` a `INTEGER`
   - Cambiado `cod_dpto` de `VARCHAR(2)` a `INTEGER`
   - Cambiado `cod_mpio` de `VARCHAR(5)` a `INTEGER`

2. **`src/data_ingestion/data_lake_loader.py`**
   - Agregado `int()` para convertir códigos antes de insertar
   - Aplicado en: `load_homicidios_initial()`, `load_homicidios_incremental()`, `load_divipola_departamentos()`, `load_divipola_municipios()`

---

## 🎯 Recomendación

**Usa la Opción 1 (Recrear)** porque:
- ✅ Más limpio y sin riesgo de errores
- ✅ Garantiza que el schema esté 100% correcto
- ✅ El código Python ya está actualizado
- ✅ Solo toma ~5 minutos recargar los datos

---

## 📝 Próximos Pasos

Después de completar esta migración:

1. ✅ Verificar que las foreign keys funcionen
2. ✅ Probar queries con JOINs
3. ✅ Configurar cron job para cargas incrementales
4. ✅ Comenzar con el ETL del Data Warehouse

---

## ❓ Troubleshooting

### Error: "violates foreign key constraint"

**Causa:** Hay códigos en `raw_homicidios` que no existen en las tablas DIVIPOLA.

**Solución:**
```sql
-- Encontrar códigos huérfanos
SELECT DISTINCT h.cod_depto
FROM raw_homicidios h
LEFT JOIN raw_divipola_departamentos d ON h.cod_depto = d.cod_dpto
WHERE d.cod_dpto IS NULL;
```

### Error: "cannot cast type varchar to integer"

**Causa:** Hay valores no numéricos en los códigos.

**Solución:**
```sql
-- Ver valores problemáticos
SELECT DISTINCT cod_depto 
FROM raw_homicidios 
WHERE cod_depto !~ '^[0-9]+$';
```

---

¡Listo! Sigue esta guía y tendrás tu Data Lake con foreign keys funcionando perfectamente. 🚀
