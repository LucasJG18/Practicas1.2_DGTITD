-- 1. gold_pib_tendencia: evolución del PIB con clasificación de ciclo económico
CREATE OR REPLACE VIEW gold_pib_tendencia AS
SELECT
    t.anio,
    m.pib_percapita_nominal,
    m.variacion_pib_pct,
    CASE
        WHEN m.variacion_pib_pct > 2  THEN 'Crecimiento fuerte'
        WHEN m.variacion_pib_pct > 0  THEN 'Crecimiento moderado'
        WHEN m.variacion_pib_pct = 0  THEN 'Estancamiento'
        ELSE 'Contracción'
    END AS clasificacion
FROM fact_macro_anual m
JOIN dim_tiempo t USING (id_tiempo)
WHERE m.id_geo = 0
ORDER BY t.anio;

-- 2. gold_empleo_tendencia: tasa de desempleo trimestral histórica
CREATE OR REPLACE VIEW gold_empleo_tendencia AS
SELECT
    t.anio,
    t.trimestre,
    ROUND(AVG(f.tasa_pct)::numeric, 2) AS tasa_desempleo_nacional
FROM fact_empleo_enemdu f
JOIN dim_tiempo t ON f.id_tiempo = t.id_tiempo
WHERE f.indicador ILIKE '%desempleo%'
  AND f.area = 'nacional'
GROUP BY t.anio, t.trimestre
ORDER BY t.anio, t.trimestre;

-- 3. gold_petroleo_30dias: promedio móvil de 30 días del WTI
CREATE OR REPLACE VIEW gold_petroleo_30dias AS
SELECT
    t.fecha,
    f.precio_petroleo_wti AS precio_diario,
    ROUND(AVG(f.precio_petroleo_wti) OVER (
        ORDER BY t.fecha
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    )::numeric, 2) AS media_movil_30d
FROM fact_indicadores_diarios f
JOIN dim_tiempo t ON f.id_tiempo = t.id_tiempo
WHERE f.precio_petroleo_wti IS NOT NULL
ORDER BY t.fecha;

-- 4. gold_empresas_provincia: empresas activas e ingresos por provincia
CREATE OR REPLACE VIEW gold_empresas_provincia AS
SELECT
    t.anio,
    g.provincia,
    COUNT(f.ruc) AS total_empresas_activas,
    SUM(f.ingresos) AS ingresos_totales
FROM fact_empresas_supercias f
JOIN dim_geografia g ON f.id_geo = g.id_geo
JOIN dim_tiempo t ON f.id_tiempo = t.id_tiempo
WHERE f.situacion_legal ILIKE '%ACTIVA%'
GROUP BY t.anio, g.provincia
ORDER BY t.anio DESC, ingresos_totales DESC;

-- 5. gold_bachilleres_vs_empresas: cruce MINEDUC + Supercias por provincia
CREATE OR REPLACE VIEW gold_bachilleres_vs_empresas AS
WITH estudiantes_provincia AS (
    SELECT id_tiempo, id_geo, SUM(total_estudiantes) AS total_estudiantes
    FROM fact_bachilleres_mineduc
    GROUP BY id_tiempo, id_geo
),
empresas_provincia AS (
    SELECT id_tiempo, id_geo, COUNT(ruc) AS total_empresas, SUM(ingresos) AS ingresos_totales
    FROM fact_empresas_supercias
    GROUP BY id_tiempo, id_geo
)
SELECT
    t.anio,
    g.provincia,
    COALESCE(e.total_estudiantes, 0) AS total_estudiantes,
    COALESCE(emp.total_empresas, 0) AS total_empresas,
    -- Ratio analítico para el dashboard:
    CASE WHEN emp.total_empresas > 0
         THEN ROUND((e.total_estudiantes::numeric / emp.total_empresas), 2)
         ELSE 0 END AS ratio_estudiantes_por_empresa
FROM dim_geografia g
JOIN dim_tiempo t ON t.id_tiempo IN (SELECT DISTINCT id_tiempo FROM estudiantes_provincia UNION SELECT DISTINCT id_tiempo FROM empresas_provincia)
LEFT JOIN estudiantes_provincia e ON g.id_geo = e.id_geo AND t.id_tiempo = e.id_tiempo
LEFT JOIN empresas_provincia emp ON g.id_geo = emp.id_geo AND t.id_tiempo = emp.id_tiempo
WHERE g.id_geo != 0 -- Omitimos el registro nacional para ver solo provincias
  AND (e.total_estudiantes IS NOT NULL OR emp.total_empresas IS NOT NULL)
ORDER BY t.anio DESC, g.provincia;

select * from gold_pib_tendencia;
select * from gold_empleo_tendencia;
select * from gold_petroleo_30dias;
select * from gold_empresas_provincia;
select * from gold_bachilleres_vs_empresas;
