# 📊 Plan de Análisis Exploratorio de Datos (EDA) - ML Homicidios

Este documento delinea la estrategia para realizar un EDA óptimo y preciso, aprovechando la arquitectura de **Data Warehouse (Modelo Estrella)** del proyecto.

---

## 1. 🚦 Auditoría de Salud del Dato (Data Profiling)

Antes de buscar insights, es crucial validar la integridad de los datos que alimentarán los modelos.

### **1.1. Integridad Temporal (Gaps)**

- **Objetivo**: Detectar fallos en la carga de datos.
- **Acción**: Cruzar `fact_homicidios` con `dim_fecha` para identificar días con **0 registros**.
- **Hipótesis**: En datos criminales nacionales, un cero absoluto suele indicar un error de ETL, no ausencia real de crimen.
- **Impacto**: Evitar sesgos en el cálculo de promedios diarios.

### **1.2. Integridad Geográfica**

- **Objetivo**: Asegurar la consistencia referencial.
- **Acción**: Verificar que todos los registros en `fact_homicidios` tengan un `cod_mpio` válido en `dim_municipio`.
- **Métrica**: % de homicidios "huérfanos" (sin municipio mapeado).

### **1.3. Análisis de Valores Nulos/Contextuales**

- **Objetivo**: Cuantificar la incertidumbre.
- **Acción**: Medir el porcentaje de:
  - Registros con `zona` (Urbana/Rural) nula.
  - Registros con `sexo` = 'NO REPORTA'.
- **Regla**: Si >5%, tratar como categoría explícita ("Silencio criminal").

---

## 2. ⏳ Análisis Temporal Multinivel ("El Cuándo")

Aprovechando los atributos ricos de `dim_fecha` (`es_festivo`, `dia_semana`, `mes`, `trimestre`).

### **2.1. Descomposición de Series de Tiempo**

- **Tendencia Secular**: Gráfico de línea anual (2003-2025). ¿La violencia es estructuralmente ascendente o descendente?
- **Estacionalidad Mensual**: Mapa de calor (**Heatmap**: Año vs. Mes). Permite ver instantáneamente si meses como **Diciembre** son sistemáticamente calientes.

### **2.2. Ciclo Semanal ("El Latido de la Violencia")**

- **Visualización**: Gráfico de violín o barras con intervalos de confianza.
- **Comparativa**: Promedio homicidios **Días Laborales (L-J)** vs. **Fin de Semana (V-D)**.

### **2.3. Efecto Calendario (Feature Engineering)**

- **Hipótesis**: _"¿Se mata más en festivos?"_
- **Acción**: Test de hipótesis visual (Boxplot) comparando `es_festivo = TRUE` vs `FALSE`.
- **Valor**: Validar si la bandera de festivo es una variable predictora fuerte.

---

## 3. 🗺️ Análisis Geoespacial ("El Dónde")

Utilizando `dim_municipio` que ya contiene coordenadas (`latitud`, `longitud`).

### **3.1. Clusters de Violencia (Hotspots)**

- **Herramienta**: Mapas de densidad (Density Heatmap) con **Plotly**.
- **Objetivo**: Identificar focos de violencia regional que ignoran fronteras departamentales (ej. Bajo Cauca, Catatumbo, Frontera con Venezuela).

### **3.2. Ranking Pareto (80/20)**

- **Objetivo**: Focalización.
- **Visualización**: Gráfico de barras acumulativo.
- **Pregunta**: ¿Qué porcentaje de municipios concentra el 80% de los homicidios?

### **3.3. Dinámica Urbano vs. Rural**

- **Variable**: Columna `zona` en `fact_homicidios`.
- **Análisis**: Series de tiempo comparativas.
- **Hipótesis**: La violencia rural obedece a ciclos distintos (ej. días de mercado, conflicto armado) que la urbana (ocio, fin de semana).

---

## 4. 👥 Análisis Demográfico ("El Quién")

Utilizando `dim_sexo`.

### **4.1. Evolución de la Brecha de Género**

- **Visualización**: Dos series temporales lineales (Hombres vs. Mujeres) en el mismo eje o ejes duales.
- **Objetivo**: Detectar si las curvas están correlacionadas o si existen periodos donde la violencia contra la mujer se desacopla de la tendencia general (alertas de feminicidio).

---

## 5. 🔍 Análisis Multivariado (Insights Avanzados)

Cruces de variables para encontrar predictores fuertes.

### **5.1. Evolución Espacio-Temporal**

- **Visualización**: Mapa animado (Slider por Año).
- **Objetivo**: Ver cómo se ha desplazado el "centro de gravedad" de la violencia en Colombia en los últimos 20 años.

### **5.2. Matriz de Riesgo (Día vs. Zona)**

- **Visualización**: Heatmap (`Dia_Semana` vs `Zona`).
- **Pregunta**: ¿Cambia el día más peligroso dependiendo de si estás en zona rural o urbana?

---

## 🛠️ Estrategia Técnica de Ejecución

Para garantizar un EDA **óptimo** en consumo de recursos:

1.  **Push-down Aggregation (SQL First)**

    - **NO HACER**: `SELECT * FROM fact_homicidios` (~330k filas a Pandas).
    - **HACER**: Delegar la agregación a la base de datos.
    - _Ejemplo_: `SELECT fecha, zona, COUNT(*) FROM fact_homicidios GROUP BY 1, 2`.

2.  **Visualización Interactiva**
    - Usar **Plotly Express** para mapas y series temporales largas.
    - Habilitar **Zoom** y **Tooltips** para explorar 20 años de historia sin perder detalle.
