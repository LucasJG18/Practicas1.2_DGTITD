-- 1. CREAR DIMENSIONES
CREATE TABLE dim_tiempo (
    id_tiempo SERIAL PRIMARY KEY,
    fecha DATE,
    anio INT,
    mes INT,
    trimestre INT
);

CREATE TABLE dim_geografia (
    id_geo INT PRIMARY KEY,
    provincia TEXT,
    cod_provincia INT,
    canton TEXT,
    cod_canton INT
);

-- Insertar el registro comodín para "Nivel Nacional" (id_geo = 0) que usa el BCE
INSERT INTO dim_geografia (id_geo, provincia, cod_provincia, canton, cod_canton)
VALUES (0, 'NACIONAL', 0, 'NACIONAL', 0) ON CONFLICT DO NOTHING;

-- 2. CREAR TABLAS DE HECHOS
CREATE TABLE fact_empleo_enemdu (
    id SERIAL PRIMARY KEY,
    id_tiempo INT REFERENCES dim_tiempo(id_tiempo),
    indicador TEXT,
    area TEXT,
    tasa_pct FLOAT
);

CREATE TABLE fact_censo_actividad (
    id SERIAL PRIMARY KEY,
    id_geo INT REFERENCES dim_geografia(id_geo),
    sexo TEXT,
    grupo_edad TEXT,
    personas_ocupadas INT,
    ciiu_codigo TEXT
);

CREATE TABLE fact_empresas_supercias (
    id SERIAL PRIMARY KEY,
    id_tiempo INT REFERENCES dim_tiempo(id_tiempo),
    id_geo INT REFERENCES dim_geografia(id_geo),
    ruc TEXT,
    nombre_empresa TEXT,
    situacion_legal TEXT,
    ingresos FLOAT,
    activos FLOAT,
    ciiu_codigo TEXT
);

CREATE TABLE fact_bachilleres_mineduc (
    id SERIAL PRIMARY KEY,
    id_tiempo INT REFERENCES dim_tiempo(id_tiempo),
    id_geo INT REFERENCES dim_geografia(id_geo),
    amie_codigo TEXT,
    nombre_institucion TEXT,
    sostenimiento TEXT,
    total_estudiantes INT
);

CREATE TABLE fact_indicadores_diarios (
    id_tiempo INT REFERENCES dim_tiempo(id_tiempo),
    precio_petroleo_wti FLOAT,
    iee_global FLOAT
);

CREATE TABLE fact_macro_anual (
    id_tiempo INT REFERENCES dim_tiempo(id_tiempo),
    id_geo INT REFERENCES dim_geografia(id_geo),
    pib_percapita_nominal FLOAT,
    variacion_pib_pct FLOAT,
    ciiu_sector TEXT,
    vab_industria_musd FLOAT
);
