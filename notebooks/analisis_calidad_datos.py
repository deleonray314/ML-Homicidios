# ============================================================================
# ANÁLISIS DE CALIDAD DE DATOS - PROYECTO ML-HOMICIDIOS
# ============================================================================
# Este archivo contiene todo el código para análisis de calidad de datos
# Copiar y pegar cada sección en celdas del notebook EDA.ipynb
# ============================================================================

# ============================================================================
# SECCIÓN 1: ANÁLISIS DE VALORES NULOS Y FALTANTES
# ============================================================================

# --- CELDA MARKDOWN ---
"""
## 1. 📊 Análisis de Calidad de Datos

### 1.1 Valores Nulos y Faltantes

Verificaremos la completitud de los datos en todas las tablas del Data Warehouse.
"""

# --- CELDA DE CÓDIGO ---
# Analizar valores nulos en cada tabla
print("=" * 80)
print("ANÁLISIS DE VALORES NULOS POR TABLA")
print("=" * 80)

tablas = ['dim_fecha', 'dim_departamento', 'dim_municipio', 'dim_sexo', 'fact_homicidios']

resultados_nulos = {}
for tabla in tablas:
    print(f"\n📋 Tabla: {tabla}")
    print("-" * 80)
    
    # Contar total de registros
    count_query = f"SELECT COUNT(*) as total FROM {tabla};"
    total = pd.read_sql(count_query, engine).iloc[0, 0]
    
    # Analizar nulos por columna
    query = f"""
    SELECT 
        column_name
    FROM information_schema.columns
    WHERE table_name = '{tabla}'
        AND table_schema = 'public'
    ORDER BY ordinal_position;
    """
    columnas = pd.read_sql(query, engine)
    
    # Para cada columna, contar nulos
    nulos_info = []
    for col in columnas['column_name']:
        null_query = f"""
        SELECT 
            COUNT(*) as total,
            COUNT({col}) as no_nulos,
            COUNT(*) - COUNT({col}) as nulos,
            ROUND(100.0 * (COUNT(*) - COUNT({col})) / COUNT(*), 2) as porcentaje_nulos
        FROM {tabla};
        """
        result = pd.read_sql(null_query, engine).iloc[0]
        nulos_info.append({
            'columna': col,
            'total': result['total'],
            'nulos': result['nulos'],
            'porcentaje_nulos': result['porcentaje_nulos']
        })
    
    df_nulos = pd.DataFrame(nulos_info)
    resultados_nulos[tabla] = df_nulos
    
    # Mostrar solo columnas con nulos
    df_con_nulos = df_nulos[df_nulos['nulos'] > 0]
    if len(df_con_nulos) > 0:
        print(df_con_nulos.to_string(index=False))
        print(f"\n⚠️  {len(df_con_nulos)} columnas con valores nulos")
    else:
        print("✅ No hay valores nulos en esta tabla")
    
    print(f"📊 Total de registros: {total:,}")

# Resumen general
print("\n" + "=" * 80)
print("RESUMEN DE COMPLETITUD")
print("=" * 80)
for tabla, df in resultados_nulos.items():
    total_columnas = len(df)
    columnas_con_nulos = len(df[df['nulos'] > 0])
    completitud = 100 - df['porcentaje_nulos'].mean()
    print(f"{tabla:25} | Completitud: {completitud:6.2f}% | Columnas con nulos: {columnas_con_nulos}/{total_columnas}")

# --- CELDA DE VISUALIZACIÓN ---
# Visualización de valores nulos
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle('Análisis de Valores Nulos por Tabla', fontsize=16, fontweight='bold')

for idx, (tabla, df_nulos) in enumerate(resultados_nulos.items()):
    row = idx // 3
    col = idx % 3
    ax = axes[row, col]
    
    # Filtrar solo columnas con nulos
    df_plot = df_nulos[df_nulos['nulos'] > 0]
    
    if len(df_plot) > 0:
        ax.barh(df_plot['columna'], df_plot['porcentaje_nulos'], color='coral')
        ax.set_xlabel('% Valores Nulos')
        ax.set_title(f'{tabla}', fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
    else:
        ax.text(0.5, 0.5, '✅ Sin valores nulos', 
                ha='center', va='center', fontsize=12, transform=ax.transAxes)
        ax.set_title(f'{tabla}', fontweight='bold')
        ax.axis('off')

# Eliminar subplot vacío si hay menos de 6 tablas
if len(resultados_nulos) < 6:
    fig.delaxes(axes[1, 2])

plt.tight_layout()
plt.show()


# ============================================================================
# SECCIÓN 2: DETECCIÓN DE DUPLICADOS
# ============================================================================

# --- CELDA MARKDOWN ---
"""
### 1.2 Detección de Duplicados

Verificaremos si existen registros duplicados en las claves primarias y en la tabla de hechos.
"""

# --- CELDA DE CÓDIGO ---
print("=" * 80)
print("ANÁLISIS DE DUPLICADOS")
print("=" * 80)

# 1. Verificar duplicados en claves primarias
print("\n📌 1. Verificación de Claves Primarias")
print("-" * 80)

verificaciones_pk = {
    'dim_fecha': 'fecha_key',
    'dim_departamento': 'cod_depto',
    'dim_municipio': 'cod_mpio',
    'dim_sexo': 'sexo_key',
    'fact_homicidios': 'homicidio_key'
}

for tabla, pk in verificaciones_pk.items():
    query = f"""
    SELECT 
        COUNT(*) as total_registros,
        COUNT(DISTINCT {pk}) as valores_unicos,
        COUNT(*) - COUNT(DISTINCT {pk}) as duplicados
    FROM {tabla};
    """
    result = pd.read_sql(query, engine).iloc[0]
    
    if result['duplicados'] > 0:
        print(f"⚠️  {tabla:25} | Duplicados en PK: {result['duplicados']}")
    else:
        print(f"✅ {tabla:25} | Sin duplicados en PK")

# 2. Verificar duplicados en fact_homicidios por combinación de dimensiones
print("\n📌 2. Duplicados en fact_homicidios (por combinación de dimensiones)")
print("-" * 80)

query_duplicados_fact = """
SELECT 
    fecha_key,
    cod_depto,
    cod_mpio,
    sexo_key,
    zona,
    COUNT(*) as ocurrencias
FROM fact_homicidios
GROUP BY fecha_key, cod_depto, cod_mpio, sexo_key, zona
HAVING COUNT(*) > 1
ORDER BY ocurrencias DESC
LIMIT 10;
"""

df_duplicados = pd.read_sql(query_duplicados_fact, engine)

if len(df_duplicados) > 0:
    print(f"⚠️  Se encontraron {len(df_duplicados)} combinaciones duplicadas")
    print("\nTop 10 combinaciones más duplicadas:")
    print(df_duplicados.to_string(index=False))
else:
    print("✅ No hay duplicados por combinación de dimensiones")

# 3. Verificar duplicados exactos en fact_homicidios
print("\n📌 3. Registros Completamente Duplicados en fact_homicidios")
print("-" * 80)

query_duplicados_exactos = """
WITH duplicados AS (
    SELECT 
        fecha_key,
        cod_depto,
        cod_mpio,
        sexo_key,
        zona,
        cantidad,
        COUNT(*) as ocurrencias
    FROM fact_homicidios
    GROUP BY fecha_key, cod_depto, cod_mpio, sexo_key, zona, cantidad
    HAVING COUNT(*) > 1
)
SELECT 
    COUNT(*) as combinaciones_duplicadas,
    SUM(ocurrencias) as total_registros_duplicados
FROM duplicados;
"""

df_dup_exactos = pd.read_sql(query_duplicados_exactos, engine).iloc[0]

if df_dup_exactos['combinaciones_duplicadas'] and df_dup_exactos['combinaciones_duplicadas'] > 0:
    print(f"⚠️  {df_dup_exactos['combinaciones_duplicadas']} combinaciones duplicadas")
    print(f"⚠️  {df_dup_exactos['total_registros_duplicados']} registros totales afectados")
else:
    print("✅ No hay registros completamente duplicados")


# ============================================================================
# SECCIÓN 3: VALIDACIÓN DE RANGOS Y TIPOS
# ============================================================================

# --- CELDA MARKDOWN ---
"""
### 1.3 Validación de Rangos y Tipos de Datos

Verificaremos que los valores estén dentro de rangos esperados y sean consistentes.
"""

# --- CELDA DE CÓDIGO ---
print("=" * 80)
print("VALIDACIÓN DE RANGOS Y TIPOS DE DATOS")
print("=" * 80)

# 1. Validar rangos de fechas
print("\n📅 1. Validación de dim_fecha")
print("-" * 80)

query_fechas = """
SELECT 
    MIN(año) as año_min,
    MAX(año) as año_max,
    MIN(mes) as mes_min,
    MAX(mes) as mes_max,
    MIN(dia) as dia_min,
    MAX(dia) as dia_max,
    COUNT(CASE WHEN mes < 1 OR mes > 12 THEN 1 END) as meses_invalidos,
    COUNT(CASE WHEN dia < 1 OR dia > 31 THEN 1 END) as dias_invalidos
FROM dim_fecha;
"""

df_fechas = pd.read_sql(query_fechas, engine).iloc[0]
print(f"Rango de años: {df_fechas['año_min']} - {df_fechas['año_max']}")
print(f"Rango de meses: {df_fechas['mes_min']} - {df_fechas['mes_max']}")
print(f"Rango de días: {df_fechas['dia_min']} - {df_fechas['dia_max']}")

if df_fechas['meses_invalidos'] > 0 or df_fechas['dias_invalidos'] > 0:
    print(f"⚠️  Meses inválidos: {df_fechas['meses_invalidos']}")
    print(f"⚠️  Días inválidos: {df_fechas['dias_invalidos']}")
else:
    print("✅ Todos los valores de fecha son válidos")

# 2. Validar códigos DIVIPOLA
print("\n🗺️  2. Validación de Códigos DIVIPOLA")
print("-" * 80)

query_deptos = """
SELECT 
    COUNT(*) as total_departamentos,
    MIN(cod_depto) as cod_min,
    MAX(cod_depto) as cod_max,
    COUNT(DISTINCT cod_depto) as codigos_unicos
FROM dim_departamento;
"""

df_deptos = pd.read_sql(query_deptos, engine).iloc[0]
print(f"Departamentos: {df_deptos['total_departamentos']} registros")
print(f"Códigos únicos: {df_deptos['codigos_unicos']}")
print(f"Rango: {df_deptos['cod_min']} - {df_deptos['cod_max']}")

if df_deptos['total_departamentos'] == 33:
    print("✅ Cantidad correcta de departamentos (33)")
else:
    print(f"⚠️  Se esperaban 33 departamentos, se encontraron {df_deptos['total_departamentos']}")

# Municipios
query_mpios = """
SELECT 
    COUNT(*) as total_municipios,
    COUNT(DISTINCT cod_mpio) as codigos_unicos,
    COUNT(CASE WHEN cod_mpio < 1000 OR cod_mpio > 99999 THEN 1 END) as codigos_fuera_rango
FROM dim_municipio;
"""

df_mpios = pd.read_sql(query_mpios, engine).iloc[0]
print(f"\nMunicipios: {df_mpios['total_municipios']} registros")
print(f"Códigos únicos: {df_mpios['codigos_unicos']}")

if df_mpios['codigos_fuera_rango'] > 0:
    print(f"⚠️  {df_mpios['codigos_fuera_rango']} códigos fuera de rango")
else:
    print("✅ Todos los códigos de municipio están en rango válido")

# 3. Validar categorías de sexo
print("\n👤 3. Validación de dim_sexo")
print("-" * 80)

query_sexo = """
SELECT 
    sexo,
    COUNT(*) as registros
FROM dim_sexo
ORDER BY sexo;
"""

df_sexo = pd.read_sql(query_sexo, engine)
print("Categorías encontradas:")
print(df_sexo.to_string(index=False))

# 4. Validar zona en fact_homicidios
print("\n🏙️  4. Validación de Zona en fact_homicidios")
print("-" * 80)

query_zona = """
SELECT 
    zona,
    COUNT(*) as cantidad,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as porcentaje
FROM fact_homicidios
GROUP BY zona
ORDER BY cantidad DESC;
"""

df_zona = pd.read_sql(query_zona, engine)
print("Distribución por zona:")
print(df_zona.to_string(index=False))

# 5. Validar cantidad en fact_homicidios
print("\n🔢 5. Validación de Cantidad en fact_homicidios")
print("-" * 80)

query_cantidad = """
SELECT 
    MIN(cantidad) as min_cantidad,
    MAX(cantidad) as max_cantidad,
    AVG(cantidad) as promedio,
    COUNT(CASE WHEN cantidad <= 0 THEN 1 END) as cantidad_invalida,
    COUNT(CASE WHEN cantidad > 100 THEN 1 END) as cantidad_sospechosa
FROM fact_homicidios;
"""

df_cantidad = pd.read_sql(query_cantidad, engine).iloc[0]
print(f"Rango de cantidad: {df_cantidad['min_cantidad']} - {df_cantidad['max_cantidad']}")
print(f"Promedio: {df_cantidad['promedio']:.2f}")

if df_cantidad['cantidad_invalida'] > 0:
    print(f"⚠️  {df_cantidad['cantidad_invalida']} registros con cantidad <= 0")
else:
    print("✅ Todas las cantidades son positivas")

if df_cantidad['cantidad_sospechosa'] > 0:
    print(f"⚠️  {df_cantidad['cantidad_sospechosa']} registros con cantidad > 100 (revisar)")


# ============================================================================
# SECCIÓN 4: CONSISTENCIA ENTRE TABLAS
# ============================================================================

# --- CELDA MARKDOWN ---
"""
### 1.4 Análisis de Consistencia entre Tablas

Verificaremos la integridad referencial y consistencia de las relaciones entre tablas.
"""

# --- CELDA DE CÓDIGO ---
print("=" * 80)
print("ANÁLISIS DE CONSISTENCIA ENTRE TABLAS")
print("=" * 80)

# 1. Verificar integridad referencial de fact_homicidios
print("\n🔗 1. Integridad Referencial de fact_homicidios")
print("-" * 80)

# Verificar fecha_key
query_fk_fecha = """
SELECT COUNT(*) as registros_huerfanos
FROM fact_homicidios f
LEFT JOIN dim_fecha d ON f.fecha_key = d.fecha_key
WHERE d.fecha_key IS NULL;
"""
huerfanos_fecha = pd.read_sql(query_fk_fecha, engine).iloc[0, 0]

if huerfanos_fecha > 0:
    print(f"⚠️  fecha_key: {huerfanos_fecha} registros sin match en dim_fecha")
else:
    print("✅ fecha_key: Todos los registros tienen match en dim_fecha")

# Verificar cod_depto
query_fk_depto = """
SELECT COUNT(*) as registros_huerfanos
FROM fact_homicidios f
LEFT JOIN dim_departamento d ON f.cod_depto = d.cod_depto
WHERE d.cod_depto IS NULL;
"""
huerfanos_depto = pd.read_sql(query_fk_depto, engine).iloc[0, 0]

if huerfanos_depto > 0:
    print(f"⚠️  cod_depto: {huerfanos_depto} registros sin match en dim_departamento")
else:
    print("✅ cod_depto: Todos los registros tienen match en dim_departamento")

# Verificar cod_mpio
query_fk_mpio = """
SELECT COUNT(*) as registros_huerfanos
FROM fact_homicidios f
LEFT JOIN dim_municipio m ON f.cod_mpio = m.cod_mpio
WHERE m.cod_mpio IS NULL;
"""
huerfanos_mpio = pd.read_sql(query_fk_mpio, engine).iloc[0, 0]

if huerfanos_mpio > 0:
    print(f"⚠️  cod_mpio: {huerfanos_mpio} registros sin match en dim_municipio")
else:
    print("✅ cod_mpio: Todos los registros tienen match en dim_municipio")

# Verificar sexo_key
query_fk_sexo = """
SELECT COUNT(*) as registros_huerfanos
FROM fact_homicidios f
LEFT JOIN dim_sexo s ON f.sexo_key = s.sexo_key
WHERE s.sexo_key IS NULL;
"""
huerfanos_sexo = pd.read_sql(query_fk_sexo, engine).iloc[0, 0]

if huerfanos_sexo > 0:
    print(f"⚠️  sexo_key: {huerfanos_sexo} registros sin match en dim_sexo")
else:
    print("✅ sexo_key: Todos los registros tienen match en dim_sexo")

# 2. Verificar jerarquía geográfica
print("\n🗺️  2. Jerarquía Geográfica (Municipio → Departamento)")
print("-" * 80)

query_jerarquia = """
SELECT COUNT(*) as municipios_huerfanos
FROM dim_municipio m
LEFT JOIN dim_departamento d ON m.cod_depto = d.cod_depto
WHERE d.cod_depto IS NULL;
"""
municipios_huerfanos = pd.read_sql(query_jerarquia, engine).iloc[0, 0]

if municipios_huerfanos > 0:
    print(f"⚠️  {municipios_huerfanos} municipios sin departamento asociado")
else:
    print("✅ Todos los municipios tienen departamento asociado")

# Verificar consistencia entre fact_homicidios y jerarquía
query_consistencia_geo = """
SELECT COUNT(*) as inconsistencias
FROM fact_homicidios f
JOIN dim_municipio m ON f.cod_mpio = m.cod_mpio
WHERE f.cod_depto != m.cod_depto;
"""
inconsistencias_geo = pd.read_sql(query_consistencia_geo, engine).iloc[0, 0]

if inconsistencias_geo > 0:
    print(f"⚠️  {inconsistencias_geo} registros con inconsistencia depto-municipio")
else:
    print("✅ Consistencia geográfica correcta en fact_homicidios")

# 3. Verificar dimensiones sin uso
print("\n📊 3. Dimensiones sin Uso en fact_homicidios")
print("-" * 80)

# Fechas sin uso
query_fechas_sin_uso = """
SELECT COUNT(*) as fechas_sin_uso
FROM dim_fecha d
LEFT JOIN fact_homicidios f ON d.fecha_key = f.fecha_key
WHERE f.fecha_key IS NULL;
"""
fechas_sin_uso = pd.read_sql(query_fechas_sin_uso, engine).iloc[0, 0]
print(f"Fechas sin homicidios registrados: {fechas_sin_uso}")

# Departamentos sin uso
query_deptos_sin_uso = """
SELECT 
    d.nom_depto,
    COUNT(f.homicidio_key) as total_homicidios
FROM dim_departamento d
LEFT JOIN fact_homicidios f ON d.cod_depto = f.cod_depto
GROUP BY d.cod_depto, d.nom_depto
HAVING COUNT(f.homicidio_key) = 0;
"""
df_deptos_sin_uso = pd.read_sql(query_deptos_sin_uso, engine)

if len(df_deptos_sin_uso) > 0:
    print(f"\nDepartamentos sin homicidios registrados: {len(df_deptos_sin_uso)}")
    print(df_deptos_sin_uso.to_string(index=False))
else:
    print("✅ Todos los departamentos tienen homicidios registrados")

# Municipios sin uso
query_mpios_sin_uso = """
SELECT COUNT(*) as municipios_sin_uso
FROM dim_municipio m
LEFT JOIN fact_homicidios f ON m.cod_mpio = f.cod_mpio
WHERE f.homicidio_key IS NULL;
"""
mpios_sin_uso = pd.read_sql(query_mpios_sin_uso, engine).iloc[0, 0]
print(f"\nMunicipios sin homicidios registrados: {mpios_sin_uso}")


# ============================================================================
# SECCIÓN 5: ESTADÍSTICAS DESCRIPTIVAS
# ============================================================================

# --- CELDA MARKDOWN ---
"""
### 1.5 Estadísticas Descriptivas Básicas

Análisis estadístico de las variables numéricas y distribuciones.
"""

# --- CELDA DE CÓDIGO ---
print("=" * 80)
print("ESTADÍSTICAS DESCRIPTIVAS")
print("=" * 80)

# 1. Estadísticas de fact_homicidios.cantidad
print("\n📊 1. Estadísticas de Cantidad de Homicidios")
print("-" * 80)

query_stats = """
SELECT 
    COUNT(*) as total_registros,
    SUM(cantidad) as total_victimas,
    MIN(cantidad) as min_cantidad,
    MAX(cantidad) as max_cantidad,
    ROUND(AVG(cantidad), 2) as promedio,
    ROUND(STDDEV(cantidad), 2) as desviacion_std,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY cantidad) as percentil_25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY cantidad) as mediana,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY cantidad) as percentil_75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY cantidad) as percentil_95,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY cantidad) as percentil_99
FROM fact_homicidios;
"""

df_stats = pd.read_sql(query_stats, engine).iloc[0]

print(f"Total de registros: {df_stats['total_registros']:,}")
print(f"Total de víctimas: {df_stats['total_victimas']:,}")
print(f"\nMedidas de tendencia central:")
print(f"  Promedio: {df_stats['promedio']}")
print(f"  Mediana: {df_stats['mediana']}")
print(f"\nMedidas de dispersión:")
print(f"  Desviación estándar: {df_stats['desviacion_std']}")
print(f"  Mínimo: {df_stats['min_cantidad']}")
print(f"  Máximo: {df_stats['max_cantidad']}")
print(f"\nPercentiles:")
print(f"  P25: {df_stats['percentil_25']}")
print(f"  P50 (Mediana): {df_stats['mediana']}")
print(f"  P75: {df_stats['percentil_75']}")
print(f"  P95: {df_stats['percentil_95']}")
print(f"  P99: {df_stats['percentil_99']}")

# 2. Distribución de registros por dimensión
print("\n📊 2. Distribución de Registros por Dimensión")
print("-" * 80)

# Por año
query_por_año = """
SELECT 
    f.año,
    COUNT(*) as registros,
    SUM(h.cantidad) as total_victimas
FROM fact_homicidios h
JOIN dim_fecha f ON h.fecha_key = f.fecha_key
GROUP BY f.año
ORDER BY f.año;
"""
df_por_año = pd.read_sql(query_por_año, engine)
print(f"\nRegistros por año: {len(df_por_año)} años diferentes")
print(f"Promedio de registros por año: {df_por_año['registros'].mean():.0f}")
print(f"Promedio de víctimas por año: {df_por_año['total_victimas'].mean():.0f}")

# Por departamento
query_por_depto = """
SELECT 
    COUNT(DISTINCT f.cod_depto) as departamentos_con_datos
FROM fact_homicidios f;
"""
deptos_con_datos = pd.read_sql(query_por_depto, engine).iloc[0, 0]
print(f"\nDepartamentos con datos: {deptos_con_datos}/33")

# Por sexo
query_por_sexo = """
SELECT 
    s.sexo,
    COUNT(*) as registros,
    SUM(h.cantidad) as total_victimas,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as porcentaje
FROM fact_homicidios h
JOIN dim_sexo s ON h.sexo_key = s.sexo_key
GROUP BY s.sexo
ORDER BY registros DESC;
"""
df_por_sexo = pd.read_sql(query_por_sexo, engine)
print("\nDistribución por sexo:")
print(df_por_sexo.to_string(index=False))

# 3. Detección de outliers
print("\n🔍 3. Detección de Outliers (Método IQR)")
print("-" * 80)

# Calcular IQR
Q1 = df_stats['percentil_25']
Q3 = df_stats['percentil_75']
IQR = Q3 - Q1
limite_inferior = Q1 - 1.5 * IQR
limite_superior = Q3 + 1.5 * IQR

query_outliers = f"""
SELECT 
    COUNT(CASE WHEN cantidad > {limite_superior} THEN 1 END) as outliers_superiores,
    COUNT(CASE WHEN cantidad < {limite_inferior} THEN 1 END) as outliers_inferiores,
    MAX(CASE WHEN cantidad > {limite_superior} THEN cantidad END) as max_outlier
FROM fact_homicidios;
"""

df_outliers = pd.read_sql(query_outliers, engine).iloc[0]

print(f"Límite inferior: {limite_inferior}")
print(f"Límite superior: {limite_superior}")
print(f"Outliers superiores: {df_outliers['outliers_superiores']}")
print(f"Outliers inferiores: {df_outliers['outliers_inferiores']}")
print(f"Valor máximo (outlier): {df_outliers['max_outlier']}")

# Mostrar algunos outliers extremos
query_top_outliers = f"""
SELECT 
    h.cantidad,
    f.fecha,
    d.nom_depto,
    m.nom_mpio,
    h.zona
FROM fact_homicidios h
JOIN dim_fecha f ON h.fecha_key = f.fecha_key
JOIN dim_departamento d ON h.cod_depto = d.cod_depto
JOIN dim_municipio m ON h.cod_mpio = m.cod_mpio
WHERE h.cantidad > {limite_superior}
ORDER BY h.cantidad DESC
LIMIT 10;
"""

df_top_outliers = pd.read_sql(query_top_outliers, engine)
if len(df_top_outliers) > 0:
    print("\nTop 10 outliers (casos con más víctimas):")
    print(df_top_outliers.to_string(index=False))

# --- CELDA DE VISUALIZACIÓN ---
# Visualización de distribución y outliers
fig, axes = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle('Análisis de Distribución de Cantidad de Homicidios', fontsize=16, fontweight='bold')

# Cargar datos de cantidad para visualización
query_cantidad_viz = "SELECT cantidad FROM fact_homicidios WHERE cantidad <= 20;"
df_cantidad_viz = pd.read_sql(query_cantidad_viz, engine)

# 1. Histograma
ax1 = axes[0, 0]
ax1.hist(df_cantidad_viz['cantidad'], bins=20, color='steelblue', edgecolor='black', alpha=0.7)
ax1.set_xlabel('Cantidad de Homicidios')
ax1.set_ylabel('Frecuencia')
ax1.set_title('Distribución de Cantidad (filtrado ≤ 20)')
ax1.grid(axis='y', alpha=0.3)

# 2. Boxplot
ax2 = axes[0, 1]
ax2.boxplot(df_cantidad_viz['cantidad'], vert=True)
ax2.set_ylabel('Cantidad de Homicidios')
ax2.set_title('Boxplot de Cantidad (filtrado ≤ 20)')
ax2.grid(axis='y', alpha=0.3)

# 3. Distribución por año
ax3 = axes[1, 0]
ax3.bar(df_por_año['año'], df_por_año['total_victimas'], color='coral', edgecolor='black')
ax3.set_xlabel('Año')
ax3.set_ylabel('Total de Víctimas')
ax3.set_title('Total de Víctimas por Año')
ax3.tick_params(axis='x', rotation=45)
ax3.grid(axis='y', alpha=0.3)

# 4. Distribución por sexo
ax4 = axes[1, 1]
colors = ['#3498db', '#e74c3c', '#95a5a6']
ax4.pie(df_por_sexo['total_victimas'], labels=df_por_sexo['sexo'], autopct='%1.1f%%', 
        colors=colors, startangle=90)
ax4.set_title('Distribución de Víctimas por Sexo')

plt.tight_layout()
plt.show()


# ============================================================================
# SECCIÓN 6: REPORTE DE CALIDAD
# ============================================================================

# --- CELDA MARKDOWN ---
"""
### 1.6 Reporte de Calidad de Datos

Resumen ejecutivo con las métricas clave de calidad.
"""

# --- CELDA DE CÓDIGO ---
print("=" * 80)
print("REPORTE DE CALIDAD DE DATOS - RESUMEN EJECUTIVO")
print("=" * 80)

# Calcular score de calidad por tabla
def calcular_score_calidad(tabla, df_nulos, tiene_duplicados, tiene_huerfanos):
    """
    Calcula un score de calidad (0-100) para una tabla
    """
    score = 100
    
    # Penalizar por nulos (máximo -30 puntos)
    if tabla in df_nulos:
        porcentaje_nulos_promedio = df_nulos[tabla]['porcentaje_nulos'].mean()
        score -= min(porcentaje_nulos_promedio, 30)
    
    # Penalizar por duplicados (-20 puntos)
    if tiene_duplicados:
        score -= 20
    
    # Penalizar por registros huérfanos (-30 puntos)
    if tiene_huerfanos:
        score -= 30
    
    return max(score, 0)

# Calcular scores
scores = {
    'dim_fecha': calcular_score_calidad('dim_fecha', resultados_nulos, False, False),
    'dim_departamento': calcular_score_calidad('dim_departamento', resultados_nulos, False, False),
    'dim_municipio': calcular_score_calidad('dim_municipio', resultados_nulos, False, municipios_huerfanos > 0),
    'dim_sexo': calcular_score_calidad('dim_sexo', resultados_nulos, False, False),
    'fact_homicidios': calcular_score_calidad('fact_homicidios', resultados_nulos, 
                                               len(df_duplicados) > 0,
                                               any([huerfanos_fecha, huerfanos_depto, huerfanos_mpio, huerfanos_sexo]))
}

print("\n📊 SCORES DE CALIDAD POR TABLA (0-100)")
print("-" * 80)
for tabla, score in scores.items():
    emoji = "🟢" if score >= 90 else "🟡" if score >= 70 else "🔴"
    print(f"{emoji} {tabla:25} | Score: {score:5.1f}/100")

score_promedio = sum(scores.values()) / len(scores)
print(f"\n{'='*80}")
print(f"📈 SCORE PROMEDIO DEL DATA WAREHOUSE: {score_promedio:.1f}/100")
print(f"{'='*80}")

# Resumen de problemas encontrados
print("\n⚠️  PROBLEMAS IDENTIFICADOS")
print("-" * 80)

problemas = []

# Verificar nulos
for tabla, df in resultados_nulos.items():
    columnas_con_nulos = df[df['nulos'] > 0]
    if len(columnas_con_nulos) > 0:
        for _, row in columnas_con_nulos.iterrows():
            if row['porcentaje_nulos'] > 5:  # Solo reportar si > 5%
                problemas.append(f"• {tabla}.{row['columna']}: {row['porcentaje_nulos']:.1f}% valores nulos")

# Verificar duplicados
if len(df_duplicados) > 0:
    problemas.append(f"• fact_homicidios: {len(df_duplicados)} combinaciones de dimensiones duplicadas")

# Verificar huérfanos
if huerfanos_fecha > 0:
    problemas.append(f"• fact_homicidios: {huerfanos_fecha} registros con fecha_key inválida")
if huerfanos_depto > 0:
    problemas.append(f"• fact_homicidios: {huerfanos_depto} registros con cod_depto inválido")
if huerfanos_mpio > 0:
    problemas.append(f"• fact_homicidios: {huerfanos_mpio} registros con cod_mpio inválido")
if huerfanos_sexo > 0:
    problemas.append(f"• fact_homicidios: {huerfanos_sexo} registros con sexo_key inválido")

# Verificar outliers extremos
if df_outliers['outliers_superiores'] > 0:
    problemas.append(f"• fact_homicidios: {df_outliers['outliers_superiores']} outliers detectados (cantidad > {limite_superior:.0f})")

if len(problemas) > 0:
    for problema in problemas:
        print(problema)
else:
    print("✅ No se encontraron problemas significativos")

# Recomendaciones
print("\n💡 RECOMENDACIONES")
print("-" * 80)

recomendaciones = []

if any(df[df['nulos'] > 0]['porcentaje_nulos'].max() > 10 for df in resultados_nulos.values() if len(df[df['nulos'] > 0]) > 0):
    recomendaciones.append("• Investigar y documentar razones de valores nulos en columnas con >10% faltantes")

if len(df_duplicados) > 0:
    recomendaciones.append("• Revisar y eliminar duplicados en fact_homicidios")

if any([huerfanos_fecha, huerfanos_depto, huerfanos_mpio, huerfanos_sexo]):
    recomendaciones.append("• Corregir registros huérfanos en fact_homicidios")

if df_outliers['outliers_superiores'] > 100:
    recomendaciones.append("• Validar outliers extremos con fuentes originales")

if mpios_sin_uso > 500:
    recomendaciones.append(f"• Considerar si es necesario mantener {mpios_sin_uso} municipios sin datos")

if len(recomendaciones) > 0:
    for rec in recomendaciones:
        print(rec)
else:
    print("✅ La calidad de los datos es excelente, no se requieren acciones inmediatas")

print("\n" + "=" * 80)
print("FIN DEL ANÁLISIS DE CALIDAD DE DATOS")
print("=" * 80)
